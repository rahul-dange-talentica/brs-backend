import pytest
from pydantic import ValidationError
from datetime import datetime
import uuid

from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, UserInDB


class TestUserBase:
    """Test UserBase schema validation."""
    
    def test_valid_user_base(self):
        """Test valid UserBase creation."""
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        user = UserBase(**user_data)
        
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
    
    def test_user_base_email_validation(self):
        """Test email validation in UserBase."""
        invalid_emails = [
            "invalid_email",
            "test@",
            "@example.com",
            "test..test@example.com",
            "test@.com",
            ""
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                UserBase(email=invalid_email)
            
            assert "email" in str(exc_info.value).lower()
    
    def test_user_base_optional_fields(self):
        """Test optional fields in UserBase."""
        # Only email is required
        user = UserBase(email="test@example.com")
        
        assert user.email == "test@example.com"
        assert user.first_name is None
        assert user.last_name is None
    
    def test_user_base_name_length_validation(self):
        """Test name field length validation."""
        long_name = "x" * 101  # Exceeds max_length=100
        
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="test@example.com", first_name=long_name)
        
        assert "String should have at most 100 characters" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email="test@example.com", last_name=long_name)
        
        assert "String should have at most 100 characters" in str(exc_info.value)
    
    def test_user_base_empty_string_names(self):
        """Test empty string names are allowed."""
        user = UserBase(
            email="test@example.com",
            first_name="",
            last_name=""
        )
        
        assert user.first_name == ""
        assert user.last_name == ""


class TestUserCreate:
    """Test UserCreate schema validation."""
    
    def test_valid_user_create(self):
        """Test valid UserCreate."""
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        user = UserCreate(**user_data)
        
        assert user.email == "test@example.com"
        assert user.password == "securepassword123"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
    
    def test_user_create_password_required(self):
        """Test password is required in UserCreate."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com")
        
        assert "Field required" in str(exc_info.value)
        assert "password" in str(exc_info.value)
    
    def test_user_create_password_length_validation(self):
        """Test password length validation."""
        # Too short password
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="short")
        
        assert "String should have at least 8 characters" in str(exc_info.value)
        
        # Too long password
        long_password = "x" * 129  # Exceeds max_length=128
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password=long_password)
        
        assert "String should have at most 128 characters" in str(exc_info.value)
    
    def test_user_create_minimum_password_length(self):
        """Test exactly minimum password length."""
        user = UserCreate(email="test@example.com", password="12345678")  # Exactly 8 chars
        
        assert user.password == "12345678"
    
    def test_user_create_maximum_password_length(self):
        """Test exactly maximum password length."""
        max_password = "x" * 128  # Exactly 128 chars
        user = UserCreate(email="test@example.com", password=max_password)
        
        assert user.password == max_password


class TestUserUpdate:
    """Test UserUpdate schema validation."""
    
    def test_valid_user_update(self):
        """Test valid UserUpdate."""
        update_data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "email": "updated@example.com"
        }
        
        user_update = UserUpdate(**update_data)
        
        assert user_update.first_name == "UpdatedFirst"
        assert user_update.last_name == "UpdatedLast"
        assert user_update.email == "updated@example.com"
    
    def test_user_update_all_fields_optional(self):
        """Test all fields are optional in UserUpdate."""
        user_update = UserUpdate()
        
        assert user_update.first_name is None
        assert user_update.last_name is None
        assert user_update.email is None
    
    def test_user_update_partial_fields(self):
        """Test partial field updates."""
        # Only first name
        user_update = UserUpdate(first_name="OnlyFirst")
        assert user_update.first_name == "OnlyFirst"
        assert user_update.last_name is None
        assert user_update.email is None
        
        # Only email
        user_update = UserUpdate(email="only@example.com")
        assert user_update.email == "only@example.com"
        assert user_update.first_name is None
        assert user_update.last_name is None
    
    def test_user_update_email_validation(self):
        """Test email validation in UserUpdate."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(email="invalid_email")
        
        assert "email" in str(exc_info.value).lower()
    
    def test_user_update_name_length_validation(self):
        """Test name length validation in UserUpdate."""
        long_name = "x" * 101
        
        with pytest.raises(ValidationError):
            UserUpdate(first_name=long_name)
        
        with pytest.raises(ValidationError):
            UserUpdate(last_name=long_name)


class TestUserResponse:
    """Test UserResponse schema validation."""
    
    def test_valid_user_response(self):
        """Test valid UserResponse."""
        user_id = uuid.uuid4()
        now = datetime.utcnow()
        
        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        user = UserResponse(**user_data)
        
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at == now
        assert user.updated_at == now
    
    def test_user_response_required_fields(self):
        """Test required fields in UserResponse."""
        required_fields = ["id", "email", "is_active", "created_at", "updated_at"]
        
        base_data = {
            "id": uuid.uuid4(),
            "email": "test@example.com",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        for field in required_fields:
            incomplete_data = {k: v for k, v in base_data.items() if k != field}
            
            with pytest.raises(ValidationError) as exc_info:
                UserResponse(**incomplete_data)
            
            assert field in str(exc_info.value)
    
    def test_user_response_uuid_validation(self):
        """Test UUID validation in UserResponse."""
        now = datetime.utcnow()
        
        with pytest.raises(ValidationError) as exc_info:
            UserResponse(
                id="not_a_uuid",
                email="test@example.com",
                is_active=True,
                created_at=now,
                updated_at=now
            )
        
        assert "uuid" in str(exc_info.value).lower()
    
    def test_user_response_datetime_validation(self):
        """Test datetime validation in UserResponse."""
        user_id = uuid.uuid4()
        
        # Invalid created_at
        with pytest.raises(ValidationError):
            UserResponse(
                id=user_id,
                email="test@example.com",
                is_active=True,
                created_at="not_a_datetime",
                updated_at=datetime.utcnow()
            )
        
        # Invalid updated_at
        with pytest.raises(ValidationError):
            UserResponse(
                id=user_id,
                email="test@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at="not_a_datetime"
            )


class TestUserInDB:
    """Test UserInDB schema validation."""
    
    def test_valid_user_in_db(self):
        """Test valid UserInDB."""
        user_id = uuid.uuid4()
        now = datetime.utcnow()
        
        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": "$2b$12$hash...",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        user = UserInDB(**user_data)
        
        assert user.id == user_id
        assert user.password_hash == "$2b$12$hash..."
        assert user.is_active is True
    
    def test_user_in_db_password_hash_required(self):
        """Test password_hash is required in UserInDB."""
        user_id = uuid.uuid4()
        now = datetime.utcnow()
        
        with pytest.raises(ValidationError) as exc_info:
            UserInDB(
                id=user_id,
                email="test@example.com",
                is_active=True,
                created_at=now,
                updated_at=now
            )
        
        assert "password_hash" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)


class TestUserSchemaEdgeCases:
    """Test edge cases for user schemas."""
    
    def test_unicode_characters_in_names(self):
        """Test unicode characters in names."""
        user = UserBase(
            email="test@example.com",
            first_name="João",
            last_name="Müller"
        )
        
        assert user.first_name == "João"
        assert user.last_name == "Müller"
    
    def test_special_characters_in_names(self):
        """Test special characters in names."""
        user = UserBase(
            email="test@example.com",
            first_name="Mary-Jane",
            last_name="O'Connor"
        )
        
        assert user.first_name == "Mary-Jane"
        assert user.last_name == "O'Connor"
    
    def test_whitespace_in_fields(self):
        """Test whitespace handling in fields."""
        # Leading/trailing whitespace should be preserved as Pydantic doesn't strip by default
        user = UserBase(
            email="test@example.com",
            first_name="  John  ",
            last_name="  Doe  "
        )
        
        assert user.first_name == "  John  "
        assert user.last_name == "  Doe  "
    
    def test_case_sensitive_email(self):
        """Test email case sensitivity."""
        # Pydantic V2 normalizes email domains to lowercase (RFC compliant)
        user = UserBase(email="Test.User@EXAMPLE.COM")
        
        # Domain should be normalized to lowercase, local part preserved
        assert user.email == "Test.User@example.com"
    
    def test_international_email_domains(self):
        """Test international email domains."""
        international_emails = [
            "test@例え.テスト",  # Japanese
            "user@münchen.de",  # German
            "user@пример.рф"    # Russian
        ]
        
        # Note: Pydantic's EmailStr may not support all international domains
        # This test documents current behavior
        for email in international_emails:
            try:
                user = UserBase(email=email)
                assert user.email == email
            except ValidationError:
                # International domains may not be supported
                pass
