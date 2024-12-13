from fastapi import APIRouter, HTTPException

from src.app.kpi_engine.dynamic.dynamic_engine import compute
from src.app.models.requests.rag import KPIRequest
from src.app.models.responses.rag import KPIResponse

router = APIRouter()


@router.post("/", response_model=KPIResponse)
async def get_kpi(
    request: KPIRequest,
) -> KPIResponse:
    try:
        return compute(request, chart=False)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/chart", response_model=KPIResponse)
async def get_kpi_chart(
    request: KPIRequest,
) -> KPIResponse:
    try:
        return compute(request, chart=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
