import os

import pytest

from ajera.client import AjeraClient
from ajera.schemas.employee import Employee

pytestmark: list[pytest.MarkDecorator] = [pytest.mark.integration]

REQUIRED_ENV_VARS = ("AJERA_API_URL", "AJERA_API_USERNAME", "AJERA_API_PASSWORD")


@pytest.fixture(scope="module")
def client() -> AjeraClient:
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            "Ajera integration test misconfigured; set environment variables: "
            + ", ".join(missing)
        )
    return AjeraClient()


def test_get_session_token(client: AjeraClient) -> None:
    token = client.get_session_token(api_version=1)
    assert isinstance(token, str)
    assert token


def test_list_employees(client: AjeraClient) -> None:
    employees = client.list_employees()
    assert isinstance(employees, list)
    assert all(isinstance(employee, Employee) for employee in employees)
