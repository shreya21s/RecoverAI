from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.services.hitl_service import HITLService
from app.schemas.approval import (
    HumanDecisionRequest,
    PendingApprovalSchema,
    ApprovalContextSchema,
    ApprovalResponseSchema,
    HumanDecisionResponse,
    PolicyRevalidationResponse
)

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

@router.get("/pending", response_model=List[PendingApprovalSchema])
def get_pending_approvals(db: Session = Depends(get_db)):
    """
    Returns a predictably sorted list of pending approvals (highest payment amount first).
    """
    try:
        hitl_service = HITLService()
        return hitl_service.get_pending_approvals(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending approvals: {str(e)}")

@router.get("/{case_id}", response_model=ApprovalContextSchema)
def get_approval_context(case_id: str, db: Session = Depends(get_db)):
    """
    Returns structural context for a human reviewer for a specific case.
    """
    try:
        hitl_service = HITLService()
        return hitl_service.get_approval_context(case_id, db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch approval context: {str(e)}")

@router.post("/{case_id}/approve", response_model=ApprovalResponseSchema)
def approve_case(case_id: str, request: HumanDecisionRequest, db: Session = Depends(get_db)):
    """
    Manually approves a case, revalidates policy, and safely continues workflow execution.
    """
    try:
        hitl_service = HITLService()
        result_state = hitl_service.approve_case(case_id, request.reviewer_id, request.reason, db)
        
        policy = result_state["policy"]
        action_result = result_state.get("action_result")
        
        return ApprovalResponseSchema(
            case_id=case_id,
            human_decision=HumanDecisionResponse(
                decision="APPROVED",
                reviewer_id=request.reviewer_id,
                reason=request.reason
            ),
            policy_revalidation=PolicyRevalidationResponse(
                decision=policy["decision"],
                action_allowed=policy["action_allowed"]
            ),
            action_result=action_result,
            final_status=result_state["final_status"]
        )
    except ValueError as ve:
        # Check if it was a duplicate request or validation error
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve case: {str(e)}")

@router.post("/{case_id}/reject", response_model=ApprovalResponseSchema)
def reject_case(case_id: str, request: HumanDecisionRequest, db: Session = Depends(get_db)):
    """
    Rejects a case, preventing any recovery action, and stops the case safely.
    """
    try:
        hitl_service = HITLService()
        result_state = hitl_service.reject_case(case_id, request.reviewer_id, request.reason, db)
        
        policy = result_state["policy"]
        
        return ApprovalResponseSchema(
            case_id=case_id,
            human_decision=HumanDecisionResponse(
                decision="REJECTED",
                reviewer_id=request.reviewer_id,
                reason=request.reason
            ),
            policy_revalidation=PolicyRevalidationResponse(
                decision=policy["decision"] if policy else "STOPPED",
                action_allowed=False
            ),
            action_result=None,
            final_status="STOPPED"
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject case: {str(e)}")
