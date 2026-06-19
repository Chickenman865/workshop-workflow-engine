from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional
from core.schemas import DiagnosticNode, Observation, ObservationState

class ExecutionEngine:
    def __init__(self):
        self.completed: Set[str] = set()
        self.nodes: Dict[str, DiagnosticNode] = {}
        self.audit_trail: List[dict] = []

    def add_nodes(self, nodes: List[DiagnosticNode]):
        for node in nodes:
            self.nodes[node.node_id] = node

    def is_ready(self, node: DiagnosticNode) -> bool:
        return all(p in self.completed for p in node.prerequisites)

    def get_ready_nodes(self):
        return [
            node for node in self.nodes.values()
            if node.node_id not in self.completed and self.is_ready(node)
        ]

    def log_execution(self, node_id: str, obs: Observation):
        record = {
            "timestamp": datetime.now().isoformat(),
            "node_id": node_id,
            "state": obs.state.value,
            "decision_reason": obs.decision_reason,
            "quality": obs.quality.model_dump(),
            "facts": obs.extracted_facts,
            "evidence": obs.raw_text
        }
        self.audit_trail.append(record)
        # Only mark as completed if we are moving forward
        if obs.state != ObservationState.RETEST_REQUIRED:
            self.completed.add(node_id)

class SafetyRouter:
    @staticmethod
    def evaluate(node: DiagnosticNode, obs: Observation) -> Tuple[str, Optional[str]]:
        
        # --- NEW: Process Faults (Human Error Loop-Back) ---
        if obs.state == ObservationState.RETEST_REQUIRED:
            if obs.quality.invalid_evidence:
                return (f"PROCESS ERROR (Invalid Evidence): {obs.decision_reason}\nPlease re-read the instruction and try again.", node.node_id)
            if obs.quality.missing_measurement:
                return (f"PROCESS ERROR (Missing Data): {obs.decision_reason}\nPlease clarify your observation.", node.node_id)
            return (f"PROCESS ERROR: {obs.decision_reason}\nPlease re-test and confirm.", node.node_id)


        # --- EXISTING: Vehicle Faults ---
        if obs.state == ObservationState.UNKNOWN:
            if node.fallback_recovery_node:
                return (f"Test blocked. Rerouting to fallback: {node.fallback_recovery_node}", node.fallback_recovery_node)
            return ("Critical blockage with no fallback path available. Halt execution.", None)

        if obs.state == ObservationState.NOMINAL:
            return ("Step passed successfully.", node.next_on_success)

        if obs.state in [ObservationState.FAULT, ObservationState.INTERMITTENT]:
            return (f"Issue identified ({obs.state.value}). Routing failure path. Reason: {obs.decision_reason}", node.next_on_failure)

        return ("Unhandled state.", None)