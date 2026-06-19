import json
from typing import List

from core.schemas import DiagnosticNode
from core.orchestrator import ExecutionEngine, SafetyRouter
from core.ollama_client import LocalOllamaParser

def build_mock_database() -> List[DiagnosticNode]:
    """
    Simulates a diagnostic workflow compiled from a service manual.
    """
    return [
        DiagnosticNode(
            node_id="harness_setup",
            title="PCM Breakout Connection",
            instruction="Hook up the breakout box to the PCM connector.",
            extraction_schema={
                "connection_status": "[Choose exactly one: connected, disconnected, unknown]"
            },
            expected_facts={
                "required_status": "connected"
            },
            accepted_fact_keys=["connection_status"],
            next_on_success="voltage_sweep",
            fallback_recovery_node=None
        ),

        DiagnosticNode(
            node_id="voltage_sweep",
            title="TPS Voltage Sweep Test",
            instruction="Measure throttle position signal wire. Look for a steady 0.5V at idle.",
            extraction_schema={
                "meter_behavior": "[Choose exactly one: stable, jumping, unreadable, flashing]"
            },
            expected_facts={
                "measurement": "voltage",
                "acceptable_range": [0.45, 0.55],
                "required_behavior": "stable"
            },
            accepted_fact_keys=["numeric_values", "meter_behavior"],
            prerequisites=["harness_setup"],
            next_on_success="exit_pass",
            next_on_failure="replace_sensor",
            fallback_recovery_node="alt_continuity"
        ),

        DiagnosticNode(
            node_id="alt_continuity",
            title="Backprobe Ground Check",
            instruction="Test resistance from back of connector Pin 3 directly to clean chassis ground.",
            extraction_schema={
                "meter_behavior": "[Choose exactly one: stable, jumping, unreadable, flashing]"
            },
            expected_facts={
                "measurement": "resistance",
                "required_behavior": "stable"
            },
            accepted_fact_keys=["numeric_values", "meter_behavior"],
            prerequisites=["harness_setup"],
            next_on_success="exit_pass",
            next_on_failure="replace_sensor"
        ),

        DiagnosticNode(
            node_id="replace_sensor",
            title="Replace TPS",
            instruction="Install new TPS component.",
            extraction_schema={
                "connection_status": "[Choose exactly one: completed, not_completed]"
            },
            expected_facts={
                "required_status": "completed"
            },
            accepted_fact_keys=["connection_status"]
        ),

        DiagnosticNode(
            node_id="exit_pass",
            title="Diagnostic Passed",
            instruction="No problem found. Vehicle is clear.",
            extraction_schema={
                "connection_status": "[Choose exactly one: complete]"
            },
            expected_facts={
                "required_status": "complete"
            },
            accepted_fact_keys=["connection_status"]
        )
    ]

def main():
    print("=== STARTING WORKSHOP WORKFLOW ENGINE ===")

    engine = ExecutionEngine()
    ollama_parser = LocalOllamaParser(model_name="qwen3:8b")
    engine.add_nodes(build_mock_database())
    current_node_id = "harness_setup"

    while current_node_id:
        node = engine.nodes[current_node_id]

        print("\n" + "=" * 50)
        print(f"STEP: {node.title}")
        print(f"INSTRUCTION: {node.instruction}")
        print("=" * 50)

        tech_input = input("\nEnter what you see/measure: ")

        if tech_input.lower() in ["exit", "quit"]:
            break

        print("[*] Contacting local Qwen3 model to extract facts...")

        observation = ollama_parser.parse_technician_input(node, tech_input)

        print(f"[Result] State: {observation.state.value}")
        print(f"[Reason] {observation.decision_reason}")
        print(f"[Facts] {observation.extracted_facts}")

        engine.log_execution(node.node_id, observation)
        status_msg, next_node_id = SafetyRouter.evaluate(node, observation)

        print(f"\n[System Action] {status_msg}")
        current_node_id = next_node_id

    print("\n[+] Diagnostic Session Concluded. Writing session logs to disk...")

    try:
        with open("data/session_log.json", "w") as f:
            json.dump(engine.audit_trail, f, indent=2)
        print("[Done] Session log saved to 'data/session_log.json'.")
    except FileNotFoundError:
        print("[ERROR] Could not save log. Ensure the 'data/' directory exists.")

if __name__ == "__main__":
    main()