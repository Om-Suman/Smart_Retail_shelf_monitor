from fastapi.testclient import TestClient

from src.main import app
from src.api.dependencies import initialize_services


initialize_services()

client = TestClient(app)


def test_root_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    assert response.json()["application"] == (
        "Smart Retail Shelf Monitoring"
    )


def test_health_endpoint():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_invalid_image_upload():

    response = client.post(
        "/api/v1/detect",
        files={
            "image": (
                "test.txt",
                b"not_an_image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400