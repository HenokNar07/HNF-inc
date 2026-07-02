from fastapi import APIRouter

from ..claude_client import generate_explanation
from ..schemas import ExplainRequest, ExplainResponse

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest) -> ExplainResponse:
    """Narrate an already-computed MVOResult. The client POSTs back exactly
    what /api/analyze returned -- this endpoint never recomputes anything,
    it only asks Claude to put the existing numbers into words.
    """
    explanation = generate_explanation(request.result)
    return ExplainResponse(explanation=explanation)
