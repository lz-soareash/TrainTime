from pydantic import BaseModel, ConfigDict


class PositionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SportAttributeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SportBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str | None = None


class SportDetail(SportBase):
    positions: list[PositionBase] = []
    attributes: list[SportAttributeBase] = []
