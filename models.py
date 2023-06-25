from sqlmodel import Field, SQLModel
from typing import Optional

class Buildings(SQLModel, table=True):
    osebuildingid: str = Field(primary_key=True)
    buildingtype: str
    totalghgemissions: float
