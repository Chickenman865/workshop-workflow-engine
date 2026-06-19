import json
import re
import requests
from core.schemas import Observation, DiagnosticNode, ObservationState, EvidenceQuality
from core.evaluator import evaluate_facts

class LocalOllamaParser:
    def __init__(self, model_name="qwen3:8b", host="http://localhost:11434"):
        self.model_name = model_name
        self.api_url = f"{host}/api/generate"

    def parse_technician_input(self, node: DiagnosticNode, raw_input: str) -> Observation:
        
        # --- LAYER 1: REGEX PRE-PARSER ---
        raw_numbers = re.findall(r'(\d+(?:\.\d+)?)', raw_input)
        extracted_numbers = [float(n) for n in raw_numbers]
        
        # --- LAYER 2: LLM FACT EXTRACTION ---
        prompt = f"""
        You are an automotive diagnostic extraction tool.
        Task: Extract facts from the technician's input based on the schema.
        
        Instruction given to tech: {node.instruction}
        Technician input: "{raw_input}"
        
        Schema to fill:
        {json.dumps(node.extraction_schema, indent=2)}
        
        Return ONLY valid JSON matching the schema keys. No explanations.
        """
        
        try:
            response = requests.post(self.api_url, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            })
            
            response.raise_for_status()
            llm_facts = json.loads(response.json().get("response", "{}"))
            
            print("\n--- RAW QWEN OUTPUT ---")
            print(json.dumps(llm_facts))
            print("-----------------------")
            
        except Exception as e:
            print(f"[!] LLM Extraction failed: {e}")
            llm_facts = {}

        # Merge Regex and LLM data
        facts = llm_facts
        facts["numeric_values"] = extracted_numbers

        # --- LAYER 3: DETERMINISTIC EVALUATION ---
        # Pass the whole node so the evaluator can check accepted_fact_keys
        state, quality, reason = evaluate_facts(facts, node)

        return Observation(
            node_id=node.node_id,
            state=state,
            quality=quality,
            extracted_facts=facts,
            decision_reason=reason,
            raw_text=raw_input
        )