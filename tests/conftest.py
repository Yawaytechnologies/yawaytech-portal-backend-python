"""
Test fixtures and helpers for face verification and attendance tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date

import numpy as np
import cv2

# =============================================================================
# Mock Image Generators
# =============================================================================


def create_test_image(width: int = 200, height: int = 200, face_center: bool = True) -> bytes:
    """
    Create a simple test image (grayscale) as bytes.

    Args:
        width: Image width
        height: Image height
        face_center: If True, create an image that appears to have a face region

    Returns:
        JPEG image bytes
    """
    # Create a simple grayscale image with some features
    img = np.random.randint(50, 200, (height, width), dtype=np.uint8)

    # Add a brighter region in the center (simulating a face)
    if face_center:
        center_y, center_x = height // 2, width // 2
        radius = min(width, height) // 4
        y, x = np.ogrid[:height, :width]
        mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius**2
        img[mask] = 180  # Brighter center region

    # Encode as JPEG
    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()


def create_similar_face_image(seed: int = 42) -> bytes:
    """
    Create a test image that is similar to another (for testing successful matching).
    Uses a fixed seed for reproducibility.
    """
    np.random.seed(seed)
    width, height = 200, 200
    img = np.random.randint(50, 200, (height, width), dtype=np.uint8)

    # Add a brighter region with slight variation
    center_y, center_x = height // 2, width // 2
    radius = min(width, height) // 4
    y, x = np.ogrid[:height, :width]
    mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius**2
    img[mask] = 175 + np.random.randint(-10, 10)  # Slightly different brightness

    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()


def create_different_face_image() -> bytes:
    """
    Create a test image that is different (for testing failed matching).
    """
    np.random.seed(999)  # Different seed
    width, height = 200, 200
    img = np.random.randint(10, 50, (height, width), dtype=np.uint8)  # Much darker

    # Different center position
    center_y, center_x = height // 3, width // 3
    radius = min(width, height) // 5  # Smaller region
    y, x = np.ogrid[:height, :width]
    mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius**2
    img[mask] = 100  # Different brightness pattern

    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()


def create_blank_image() -> bytes:
    """Create a blank (all white) image with no features."""
    img = np.ones((200, 200), dtype=np.uint8) * 255
    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()


# =============================================================================
# Mock FastAPI UploadFile
# =============================================================================


class MockUploadFile:
    """Mock FastAPI UploadFile for testing."""

    def __init__(
        self,
        filename: str = "selfie.jpg",
        content_type: str = "image/jpeg",
        content: bytes | None = None,
    ):
        self.filename = filename
        self.content_type = content_type
        self._content = content or create_test_image()
        self._position = 0

    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            result = self._content[self._position :]
            self._position = len(self._content)
        else:
            result = self._content[self._position : self._position + size]
            self._position += len(result)
        return result

    async def seek(self, position: int):
        self._position = position

    async def close(self):
        pass


# =============================================================================
# Mock Database Objects
# =============================================================================


def create_mock_profile_row(
    employee_id: str = "TEST001",
    profile_bucket: str = "profile_images",
    profile_path: str = "employees/TEST001/profile.jpg",
):
    """Create a mock profile row for testing."""
    mock = MagicMock()
    mock.employee_id = employee_id
    mock.profile_bucket = profile_bucket
    mock.profile_path = profile_path
    return mock


def create_mock_attendance_session(
    session_id: int = 1,
    employee_id: str = "TEST001",
    check_in_utc: datetime | None = None,
    check_out_utc: datetime | None = None,
    work_date_local: date | None = None,
):
    """Create a mock attendance session for testing."""
    mock = MagicMock()
    mock.id = session_id
    mock.employee_id = employee_id
    mock.check_in_utc = check_in_utc or datetime.utcnow()
    mock.check_out_utc = check_out_utc
    mock.work_date_local = work_date_local or date.today()
    return mock


def create_mock_evidence(
    evidence_id: int = 1, session_id: int = 1, verified: bool = False, confidence_score: float = 0.0
):
    """Create a mock evidence record for testing."""
    mock = MagicMock()
    mock.id = evidence_id
    mock.session_id = session_id
    mock.evidence_type = "check_in"
    mock.image_bucket = "daily_attandance"
    mock.image_path = f"attendance/TEST001/{date.today()}/check_in_test.jpg"
    mock.image_mime = "image/jpeg"
    mock.image_size = 10000
    mock.verified = verified
    mock.confidence_score = confidence_score
    mock.verification_notes = "Test note"
    mock.verified_at = datetime.utcnow() if verified else None
    mock.created_at = datetime.utcnow()
    return mock


# Pytest


# ============================================================================= Fixtures
# =============================================================================


@pytest.fixture
def sample_profile_image():
    """Fixture providing a sample profile image."""
    return create_test_image()


@pytest.fixture
def sample_selfie_image():
    """Fixture providing a sample selfie image."""
    return create_test_image()


@pytest.fixture
def similar_face_image():
    """Fixture providing a similar face image (should match)."""
    return create_similar_face_image()


@pytest.fixture
def different_face_image():
    """Fixture providing a different face image (should not match)."""
    return create_different_face_image()


@pytest.fixture
def blank_image():
    """Fixture providing a blank image (no features)."""
    return create_blank_image()


@pytest.fixture
def mock_profile_row():
    """Fixture providing a mock profile row."""
    return create_mock_profile_row()


@pytest.fixture
def mock_attendance_session():
    """Fixture providing a mock attendance session."""
    return create_mock_attendance_session()


@pytest.fixture
def mock_upload_file():
    """Fixture providing a mock upload file."""
    return MockUploadFile()


@pytest.fixture
def mock_db():
    """Fixture providing a mock database session."""
    mock = MagicMock()
    mock.add = MagicMock()
    mock.flush = MagicMock()
    mock.commit = MagicMock()
    mock.refresh = MagicMock()
    return mock


@pytest.fixture
def mock_supabase():
    """Fixture providing a mocked Supabase client."""
    with patch("app.services.face_verification_service.get_supabase") as mock:
        supabase_mock = MagicMock()

        # Mock storage
        storage_mock = MagicMock()
        supabase_mock.storage = storage_mock

        # Mock bucket download
        bucket_mock = MagicMock()
        storage_mock.from_ = MagicMock(return_value=bucket_mock)
        bucket_mock.download = MagicMock(return_value=create_test_image())
        bucket_mock.upload = MagicMock(return_value={"path": "test/path"})

        mock.return_value = supabase_mock
        yield mock


@pytest.fixture
def face_verification_service(mock_supabase):
    """Fixture providing a FaceVerificationService instance with mocked dependencies."""
    with patch("app.services.face_verification_service.get_supabase"):
        from app.services.face_verification_service import FaceVerificationService

        service = FaceVerificationService()
        # Override the face cascade to not require actual files
        return service
