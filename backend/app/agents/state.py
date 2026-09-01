from typing import TypedDict, List, Optional, Dict, Any

class RecoveryState(TypedDict):
    case_id: str
    payment_data: Optional[Dict[str, Any]]
    customer_data: Optional[Dict[str, Any]]
    diagnosis: Optional[Dict[str, Any]]
    customer_analysis: Optional[Dict[str, Any]]
    strategy: Optional[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]
    action_result: Optional[Dict[str, Any]]
    final_status: Optional[str]
    agent_trace: List[Dict[str, Any]]
    errors: List[str]
    human_decision: Optional[Dict[str, Any]]
    explanation: Optional[Dict[str, Any]]

