from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ObservationState(str, Enum):
    NOMINAL = "NOMINAL"
    FAULT = "FAULT"
    INTERMITTENT = "INTERMITTENT"
    UNKNOWN = "UNKNOWN"
    RETEST_REQUIRED = "RETEST_REQUIRED"

class EvidenceQuality(BaseModel):
    contradictory: bool = False
    ambiguous: bool = False
    missing_measurement: bool = False
    invalid_evidence: bool = False

class Observation(BaseModel):
    node_id: str
    state: ObservationState
    quality: EvidenceQuality
    extracted_facts: dict
    decision_reason: str
    raw_text: str

class DiagnosticNode(BaseModel):
    node_id: str
    title: str
    instruction: str
    
    extraction_schema: dict
    expected_facts: dict
    accepted_fact_keys: List[str] = Field(default_factory=list)
    
    prerequisites: List[str] = Field(default_factory=list)
    
    next_on_success: Optional[str] = None
    next_on_failure: Optional[str] = None
    fallback_recovery_node: Optional[str] = None