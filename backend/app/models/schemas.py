from pydantic import BaseModel

class Panchayat(BaseModel):
    id: str
    name: str
    district: str