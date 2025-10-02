import pytest
from pydantic import BaseModel, Field, ValidationError

from ajera.schemas.generic import GenericBaseModel, GenericRequest, GenericResponse

# =============================================================================
# TEST: Fixtures
# =============================================================================


class MockMethodArguments(BaseModel):
    username: str
    password: str


class MockContent(BaseModel):
    user_id: int
    name: str


# =============================================================================
# TEST: GenericBaseModel
# =============================================================================


class TestGenericBaseModel:
    """
    Test cases for GenericBaseModel
    """

    def test_generic_base_model_creation(self):
        class TestModel(GenericBaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42

    def test_extra_fields_ignored(self):
        class TestModel(GenericBaseModel):
            name: str

        # Should not raise an error due to extra="ignore" configuration
        model = TestModel(name="test", extra_field="ignored")
        assert model.name == "test"
        assert not hasattr(model, "extra_field")

    def test_validation_by_alias(self):
        class TestModel(GenericBaseModel):
            name: str = Field(alias="Name")

        model = TestModel(Name="test")
        assert model.name == "test"

        # Should also work with field name due to validate_by_name=True
        model = TestModel(name="test")
        assert model.name == "test"


# =============================================================================
# TEST: GenericRequest
# =============================================================================


class TestGenericRequest:
    """
    Test cases for GenericRequest
    """

    def test_basic_request_creation(self):
        method_args = MockMethodArguments(username="test_user", password="test_pass")

        request = GenericRequest[MockMethodArguments](
            method="TestMethod",
            session_token="test_token",
            method_arguments=method_args,
        )

        assert request.method == "TestMethod"
        assert request.session_token == "test_token"
        assert request.method_arguments.username == "test_user"
        assert request.method_arguments.password == "test_pass"

    def test_request_with_aliases(self):
        method_args = MockMethodArguments(username="test_user", password="test_pass")

        request = GenericRequest[MockMethodArguments](
            Method="TestMethod", SessionToken="test_token", MethodArguments=method_args
        )

        assert request.method == "TestMethod"
        assert request.session_token == "test_token"
        assert request.method_arguments.username == "test_user"

    def test_request_without_session_token(self):
        method_args = MockMethodArguments(username="test_user", password="test_pass")

        request = GenericRequest[MockMethodArguments](
            method="TestMethod", method_arguments=method_args
        )

        assert request.method == "TestMethod"
        assert request.session_token is None
        assert request.method_arguments.username == "test_user"

    def test_request_serialization(self):
        method_args = MockMethodArguments(username="test_user", password="test_pass")

        request = GenericRequest[MockMethodArguments](
            method="TestMethod",
            session_token="test_token",
            method_arguments=method_args,
        )

        # Test serialization by alias (default for API communication)
        serialized = request.model_dump(by_alias=True)
        expected = {
            "Method": "TestMethod",
            "SessionToken": "test_token",
            "MethodArguments": {"username": "test_user", "password": "test_pass"},
        }
        assert serialized == expected

    def test_request_validation_error(self):
        # Missing required method field
        with pytest.raises(ValidationError) as exc_info:
            GenericRequest[MockMethodArguments]()

        # Check that the error mentions the missing field
        assert "method" in str(exc_info.value).lower() or "Method" in str(
            exc_info.value
        )

    def test_request_with_dict_method_arguments(self):
        # Using dict type for method_arguments
        request_data = {
            "Method": "TestMethod",
            "SessionToken": "test_token",
            "MethodArguments": {"username": "test_user", "password": "test_pass"},
        }

        request = GenericRequest[MockMethodArguments].model_validate(request_data)
        assert request.method == "TestMethod"
        assert request.method_arguments.username == "test_user"


# =============================================================================
# TEST: GenericResponse
# =============================================================================


class TestGenericResponse:
    """
    Test cases for GenericResponse
    """

    def test_basic_response_creation(self):
        content = MockContent(user_id=123, name="Test User")

        response = GenericResponse[MockContent](
            response_code=200,
            message="Success",
            errors=None,
            usage_key="test-guid-123",
            content=content,
        )

        assert response.response_code == 200
        assert response.message == "Success"
        assert response.errors is None
        assert response.usage_key == "test-guid-123"
        assert response.content.user_id == 123
        assert response.content.name == "Test User"

    def test_response_with_aliases(self):
        content = MockContent(user_id=123, name="Test User")

        response = GenericResponse[MockContent](
            ResponseCode=200,
            Message="Success",
            Errors=None,
            UsageKey="test-guid-123",
            Content=content,
        )

        assert response.response_code == 200
        assert response.message == "Success"
        assert response.content.user_id == 123

    def test_response_with_errors(self):
        errors = [
            {"code": "E001", "message": "Invalid input"},
            {"code": "E002", "message": "Missing field"},
        ]

        response = GenericResponse[dict](
            response_code=400, message="Bad Request", errors=errors, content={}
        )

        assert response.response_code == 400
        assert response.message == "Bad Request"
        assert len(response.errors) == 2
        assert response.errors[0]["code"] == "E001"

    def test_response_minimal_creation(self):
        response = GenericResponse[dict]()

        assert response.response_code is None
        assert response.message is None
        assert response.errors is None
        assert response.usage_key is None
        assert response.content == {}  # default_factory=dict

    def test_response_serialization(self):
        content = MockContent(user_id=123, name="Test User")

        response = GenericResponse[MockContent](
            response_code=200, message="Success", content=content
        )

        # Test serialization by alias
        serialized = response.model_dump(by_alias=True)
        expected = {
            "ResponseCode": 200,
            "Message": "Success",
            "Errors": None,
            "UsageKey": None,
            "Content": {"user_id": 123, "name": "Test User"},
        }
        assert serialized == expected

    def test_response_with_dict_content(self):
        response_data = {
            "ResponseCode": 200,
            "Message": "Success",
            "Content": {"user_id": 123, "name": "Test User"},
        }

        response = GenericResponse[MockContent].model_validate(response_data)
        assert response.response_code == 200
        assert response.content.user_id == 123
        assert response.content.name == "Test User"

    def test_response_exclude_none_serialization(self):
        content = MockContent(user_id=123, name="Test User")

        response = GenericResponse[MockContent](response_code=200, content=content)

        # Test serialization excluding None values
        serialized = response.model_dump(by_alias=True, exclude_none=True)
        expected = {
            "ResponseCode": 200,
            "Content": {"user_id": 123, "name": "Test User"},
        }
        assert serialized == expected

    def test_response_type_validation(self):
        # Valid content type
        content = MockContent(user_id=123, name="Test User")
        response = GenericResponse[MockContent](content=content)
        assert isinstance(response.content, MockContent)

        # Test with dict that can be converted to MockContent
        response_data = {"Content": {"user_id": 123, "name": "Test User"}}
        response = GenericResponse[MockContent].model_validate(response_data)
        assert isinstance(response.content, MockContent)
        assert response.content.user_id == 123


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestGenericIntegration:
    """
    Integration tests for GenericRequest and GenericResponse together
    """

    def test_request_response_roundtrip(self):
        # Create request
        method_args = MockMethodArguments(username="test_user", password="test_pass")
        request = GenericRequest[MockMethodArguments](
            method="GetUser", session_token="session_123", method_arguments=method_args
        )

        # Create corresponding response
        content = MockContent(user_id=123, name="Test User")
        response = GenericResponse[MockContent](
            response_code=200,
            message="User retrieved successfully",
            usage_key="usage_123",
            content=content,
        )

        # Verify the roundtrip
        assert request.method == "GetUser"
        assert response.response_code == 200
        assert response.content.name == "Test User"

    def test_serialization_compatibility(self):
        # Serialize a request
        method_args = MockMethodArguments(username="api_user", password="api_pass")
        request = GenericRequest[MockMethodArguments](
            method="Login", method_arguments=method_args
        )

        request_dict = request.model_dump(by_alias=True)

        # Verify the structure is as expected for API communication
        assert "Method" in request_dict
        assert "MethodArguments" in request_dict
        assert request_dict["Method"] == "Login"
        assert request_dict["MethodArguments"]["username"] == "api_user"

    def test_generic_type_flexibility(self):
        # Test with simple dict
        dict_response = GenericResponse[dict](
            response_code=200, content={"key": "value", "number": 42}
        )
        assert dict_response.content["key"] == "value"

        # Test with list
        list_response = GenericResponse[list](
            response_code=200, content=[1, 2, 3, "test"]
        )
        assert len(list_response.content) == 4
        assert list_response.content[3] == "test"

        # Test with custom model
        model_response = GenericResponse[MockContent](
            response_code=200, content=MockContent(user_id=999, name="Model User")
        )
        assert model_response.content.user_id == 999
