from core.schemas import ObservationState, EvidenceQuality, DiagnosticNode

def evaluate_facts(
    facts: dict,
    node: DiagnosticNode
):
    quality = EvidenceQuality()
    expected_facts = node.expected_facts

    # -----------------------------
    # 0. THE GATEKEEPER: Data-Driven Evidence Validation
    # -----------------------------
    provided_keys = set()
    for key, value in facts.items():
        # Ignore empty regex arrays so they don't trigger false positives
        if key == "numeric_values" and not value:
            continue
        # If the LLM or Regex found actual data, track it
        if value is not None and value != "" and value != []:
            provided_keys.add(key)

    unexpected = provided_keys - set(node.accepted_fact_keys)
    
    # Process Fault: Wrong type of evidence provided
    if unexpected:
        quality.invalid_evidence = True
        reason = f"invalid_evidence. Expected: {node.accepted_fact_keys}, Observed unexpected: {list(unexpected)}"
        return (ObservationState.RETEST_REQUIRED, quality, reason)

    # Process Fault: Missing Data
    if not provided_keys:
        quality.missing_measurement = True
        return (ObservationState.RETEST_REQUIRED, quality, "missing_measurement. No valid data extracted.")

    values = facts.get("numeric_values", [])
    behavior = facts.get("meter_behavior", "").lower()

    # -----------------------------
    # 1. Exact Status / Connection Checks
    # -----------------------------
    if "required_status" in expected_facts:
        actual = facts.get("connection_status")

        if actual is None or actual == "unknown":
            quality.missing_measurement = True
            return (ObservationState.RETEST_REQUIRED, quality, "missing_status. Could not determine connection state.")

        if actual == expected_facts["required_status"]:
            return (ObservationState.NOMINAL, quality, "Status matches expected.")
        else:
            return (ObservationState.FAULT, quality, f"Status fault. Expected {expected_facts['required_status']}, got {actual}.")

    # -----------------------------
    # 2. Generic Measurement Checks
    # -----------------------------
    if "measurement" in expected_facts:

        # Unstable meter behavior immediately triggers intermittent
        if behavior in ["jumping", "unstable", "fluctuating", "unreadable", "flashing"]:
            return (ObservationState.INTERMITTENT, quality, f"Intermittent reading. Behavior: {behavior}.")

        # Range check (Allows multiple values, e.g., KOEO and Running)
        if "acceptable_range" in expected_facts and values:
            low, high = expected_facts["acceptable_range"]
            for v in values:
                if v < low or v > high:
                    return (ObservationState.FAULT, quality, f"Out of range. Value {v} outside [{low}, {high}].")
            
            # If we have values and they all passed the range check
            if not behavior or behavior == expected_facts.get("required_behavior", "stable"):
                 return (ObservationState.NOMINAL, quality, "Measurements within acceptable range.")

        # Behavior match (if no numbers, but behavior was requested)
        if "required_behavior" in expected_facts and behavior:
            if behavior == expected_facts["required_behavior"]:
                return (ObservationState.NOMINAL, quality, "Behavior matches expected.")
            else:
                return (ObservationState.FAULT, quality, f"Behavior fault. Expected {expected_facts['required_behavior']}, got {behavior}.")

    # -----------------------------
    # 3. Fallback: Nothing Matched
    # -----------------------------
    quality.ambiguous = True
    return (
        ObservationState.UNKNOWN,
        quality,
        "Ambiguous data. Evaluator could not match facts to expected rules."
    )