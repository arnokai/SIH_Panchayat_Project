from fastapi import APIRouter
from app.services.csv_service import get_all_panchayats
from app.models.schemas import Panchayat

router = APIRouter(
    prefix="/api/v1",
    tags=["Panchayats"]
)

@router.get("/panchayats", response_model=list[Panchayat])
def list_panchayats():
    return get_all_panchayats()
