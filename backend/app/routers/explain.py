from fastapi import APIRouter, Request

from ..explain_template import generate_explanation
from ..rate_limit import EXPLAIN_RATE_LIMIT, limiter
from ..schemas import ExplainRequest, ExplainResponse

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
@limiter.limit(EXPLAIN_RATE_LIMIT)
def explain(request: Request, body: ExplainRequest) -> ExplainResponse:
    """Narrate an already-computed MVOResult. The client POSTs back exactly
    what /api/analyze returned -- this endpoint never recomputes anything,
    it fills in a fixed prose template with the existing numbers. No
    external API call, no cost, nothing that can fail for lack of a key.

    The `request` param (unused directly) is required by slowapi's rate
    limiter, which pulls the caller's IP from it.
    """
    explanation = generate_explanation(body.result)
    return ExplainResponse(explanation=explanation)
