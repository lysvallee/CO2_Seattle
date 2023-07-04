from sqlmodel import Field, SQLModel
from typing import Optional

class Buildings(SQLModel, table=True):
    osebuildingid: str = Field(primary_key=True)
    buildingtype: str
    primarypropertytype: str
    zipcode: float
    taxparcelidentificationnumber: str
    councildistrictcode: int
    neighborhood: str
    latitude: float
    longitude: float
    yearbuilt: int
    numberofbuildings: int
    numberoffloors: int
    propertygfatotal: int
    propertygfaparking: int
    propertygfabuilding_s: int
    listofallpropertyusetypes: str
    largestpropertyusetype: str
    largestpropertyusetypegfa: float
    secondlargestpropertyusetype: str
    secondlargestpropertyusetypegfa: float
    thirdlargestpropertyusetype: str
    thirdlargestpropertyusetypegfa: float
    yearsenergystarcertified: float
    energystarscore: str
    siteeui_kbtu_sf: float
    siteeuiwn_kbtu_sf: float
    sourceeui_kbtu_sf: float
    sourceeuiwn_kbtu_sf: float
    siteenergyuse_kbtu: float
    siteenergyusewn_kbtu: float
    steamuse_kbtu: float
    electricity_kbtu: float
    naturalgas_kbtu: float
    defaultdata: bool
    compliancestatus: str    
    outlier: str
    totalghgemissions: float
