import json
from pathlib import Path
from typing import cast

from app import app
from fastapi import FastAPI

from openapi_python.generator import GenerationRequest, generate_client

OUTPUT_DIR = Path(__file__).parent / "generated"


def _service_b_openapi() -> dict:
    from generated.service_a_client.types import CiscoAccessPointConfig, PetEnvelope

    service_b = FastAPI(separate_input_output_schemas=False)

    @service_b.get("/pets/{pet_id}", response_model=PetEnvelope)
    def get_pet(pet_id: int) -> PetEnvelope:
        return cast(
            PetEnvelope,
            {"pet": {"pet_type": "cat", "lives": 9}, "request_id": f"pet_{pet_id}"},
        )

    @service_b.post("/pets", response_model=PetEnvelope)
    def create_pet(body: PetEnvelope) -> PetEnvelope:
        return body

    @service_b.post("/sites", response_model=CiscoAccessPointConfig)
    def create_site(body: CiscoAccessPointConfig) -> CiscoAccessPointConfig:
        return body

    return service_b.openapi()


def main() -> None:
    generate_client(
        GenerationRequest(
            output_dir=OUTPUT_DIR,
            package_name="service_a_client",
            spec_json=json.dumps(app.openapi()),
            overwrite=True,
        )
    )
    generate_client(
        GenerationRequest(
            output_dir=OUTPUT_DIR,
            spec_json=json.dumps(_service_b_openapi()),
            overwrite=True,
        )
    )


if __name__ == "__main__":
    main()
