from __future__ import annotations

from typing import Annotated, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(separate_input_output_schemas=False)


class Cat(BaseModel):
    pet_type: Literal["cat"]
    lives: int


class Dog(BaseModel):
    pet_type: Literal["dog"]
    bark_volume: int


Pet = Annotated[Cat | Dog, Field(discriminator="pet_type")]


class PetEnvelope(BaseModel):
    pet: Pet
    request_id: str


@app.get("/pets/{pet_id}", response_model=PetEnvelope)
def get_pet(pet_id: int) -> PetEnvelope:
    return PetEnvelope(pet=Cat(pet_type="cat", lives=9), request_id=f"pet_{pet_id}")


@app.post("/pets", response_model=PetEnvelope)
def create_pet(body: PetEnvelope) -> PetEnvelope:
    return body


class CiscoSiteArea(BaseModel):
    type: Literal["area"]
    name: str


class CiscoSiteBuilding(BaseModel):
    type: Literal["building"]
    name: str
    country: str


class CiscoSiteFloor(BaseModel):
    type: Literal["floor"]
    name: str
    floor_number: int


type CiscoSite = Annotated[
    CiscoSiteArea | CiscoSiteBuilding | CiscoSiteFloor,
    Field(discriminator="type"),
]


class CiscoAccessPointConfig(BaseModel):
    site_hierarchy: list[CiscoSite]


@app.post("/sites", response_model=CiscoAccessPointConfig)
def create_site(body: CiscoAccessPointConfig) -> CiscoAccessPointConfig:
    return body
