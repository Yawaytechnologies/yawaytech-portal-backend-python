"""
Unit tests for FaceVerificationService.

These tests verify the face verification logic without requiring
actual database or Supabase connections.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.face_verification_service import (
    FaceVerificationService,
    SIMILARITY_THRESHOLD,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_profile_repo():
    """Mock EmployeeProfileRepo."""
    with patch("app.services.face_verification_service.EmployeeProfileRepo") as mock:
        repo_mock = MagicMock()
        mock.return_value = repo_mock
        yield repo_mock


@pytest.fixture
def mock_attendance_repo():
    """Mock AttendanceRepository."""
    with patch("app.services.face_verification_service.AttendanceRepository") as mock:
        repo_mock = MagicMock()
        mock.return_value = repo_mock
        yield repo_mock


@pytest.fixture
def service(mock_profile_repo, mock_attendance_repo):
    """Create FaceVerificationService with mocked dependencies."""
    with patch("app.services.face_verification_service.get_supabase"):
        svc = FaceVerificationService()
        return svc


# =============================================================================
# Test: Face Comparison Logic (internal _compare_faces method)
# =============================================================================


class TestCompareFaces:
    """Tests for the _compare_faces internal method."""

    def test_compare_faces_returns_tuple(self, service):
        """Test that _compare_faces returns a tuple of (bool, float)."""
        # Create two test images
        import numpy as np
        import cv2

        # Create simple test images
        img1 = np.random.randint(50, 200, (200, 200), dtype=np.uint8)
        img2 = np.random.randint(50, 200, (200, 200), dtype=np.uint8)

        _, encoded1 = cv2.imencode(".jpg", img1)
        _, encoded2 = cv2.imencode(".jpg", img2)

        bytes1 = encoded1.tobytes()
        bytes2 = encoded2.tobytes()

        result = service._compare_faces(bytes1, bytes2)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)  # is_match
        assert isinstance(result[1], float)  # similarity_score

    def test_compare_faces_with_blank_images_returns_no_match(self, service, blank_image):
        """Test that blank images (no features) return no match."""
        result = service._compare_faces(blank_image, blank_image)

        is_match, similarity = result
        assert is_match is False
        assert similarity == 0.0


# =============================================================================
# Test: verify_face method - Employee not found
# =============================================================================


class TestVerifyFaceEmployeeNotFound:
    """Tests for verify_face when employee has no profile."""

    def test_no_profile_returns_failure(self, service, mock_profile_repo, mock_db):
        """Test that verification fails when employee has no profile image."""
        # Setup: Employee has no profile
        mock_profile_repo.get_by_employee_id.return_value = None

        # Create test selfie
        from tests.conftest import create_test_image

        selfie = create_test_image()

        # Execute
        result = service.verify_face(
            db=mock_db,
            employee_id="NO_PROFILE_001",
            selfie_image_data=selfie,
            selfie_mime="image/jpeg",
        )

        # Assert
        assert result["verified"] is False
        assert result["confidence_score"] == 0.0
        assert "No profile image found" in result["message"]
        assert (
            "not enrolled" in result["error"].lower()
            or "not enrolled" in result["debug_note"].lower()
        )


# =============================================================================
# Test: verify_face method - Profile download failure
# =============================================================================


class TestVerifyFaceProfileDownload:
    """Tests for verify_face when profile image download fails."""

    def test_profile_download_failure(self, service, mock_profile_repo, mock_db):
        """Test that verification fails when profile image cannot be downloaded."""
        from tests.conftest import create_mock_profile_row, create_test_image

        # Setup: Profile exists but download fails
        mock_profile = create_mock_profile_row()
        mock_profile_repo.get_by_employee_id.return_value = mock_profile

        with patch.object(
            service, "_download_image_from_storage", side_effect=Exception("Download failed")
        ):
            selfie = create_test_image()

            result = service.verify_face(
                db=mock_db,
                employee_id="TEST001",
                selfie_image_data=selfie,
                selfie_mime="image/jpeg",
            )

        # Assert
        assert result["verified"] is False
        assert result["confidence_score"] == 0.0
        assert "Failed to retrieve profile image" in result["message"]


# =============================================================================
# Test: verify_face method - Successful verification
# =============================================================================


class TestVerifyFaceSuccess:
    """Tests for successful face verification."""

    def test_verification_with_valid_images(self, service, mock_profile_repo, mock_db):
        """Test face verification with valid images returns proper result."""
        from tests.conftest import create_mock_profile_row, create_test_image

        # Setup: Profile exists
        mock_profile = create_mock_profile_row()
        mock_profile_repo.get_by_employee_id.return_value = mock_profile

        # Mock the download to return a test image
        with patch.object(
            service, "_download_image_from_storage", return_value=create_test_image()
        ):
            selfie = create_test_image()

            result = service.verify_face(
                db=mock_db,
                employee_id="TEST001",
                selfie_image_data=selfie,
                selfie_mime="image/jpeg",
            )

        # Assert - result structure is correct
        assert "verified" in result
        assert "confidence_score" in result
        assert "message" in result
        assert isinstance(result["verified"], bool)
        assert isinstance(result["confidence_score"], float)
        assert 0.0 <= result["confidence_score"] <= 1.0


# =============================================================================
# Test: verify_face method - Response structure
# =============================================================================


class TestVerifyFaceResponseStructure:
    """Tests for verify_face response structure."""

    def test_response_has_required_fields(self, service, mock_profile_repo, mock_db):
        """Test that verify_face returns all required fields."""
        from tests.conftest import create_mock_profile_row, create_test_image

        # Setup
        mock_profile = create_mock_profile_row()
        mock_profile_repo.get_by_employee_id.return_value = mock_profile

        with patch.object(
            service, "_download_image_from_storage", return_value=create_test_image()
        ):
            selfie = create_test_image()

            result = service.verify_face(
                db=mock_db,
                employee_id="TEST001",
                selfie_image_data=selfie,
                selfie_mime="image/jpeg",
            )

        # Assert all required fields exist
        required_fields = [
            "verified",
            "confidence_score",
            "distance",
            "message",
            "profile_path",
            "error",
            "debug_note",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"


# =============================================================================
# Test: save_evidence method
# =============================================================================


class TestSaveEvidence:
    """Tests for the save_evidence method."""

    def test_save_evidence_returns_evidence_object(self, service, mock_db, mock_attendance_repo):
        """Test that save_evidence creates an evidence record."""
        from tests.conftest import create_mock_attendance_session
        from app.data.models.attendance_evidence import EvidenceType

        # Setup
        mock_session = create_mock_attendance_session()
        mock_attendance_repo.get_session_by_id.return_value = mock_session

        with patch("app.services.face_verification_service.get_supabase") as mock_supabase:
            mock_bucket = MagicMock()
            mock_bucket.upload.return_value = {"path": "test/path"}
            mock_storage = MagicMock()
            mock_storage.from_.return_value = mock_bucket
            mock_supabase.return_value.storage = mock_storage

            from tests.conftest import create_test_image

            image_data = create_test_image()

            result = service.save_evidence(
                db=mock_db,
                session_id=1,
                evidence_type=EvidenceType.CHECK_IN,
                image_data=image_data,
                image_mime="image/jpeg",
                verified=True,
                confidence_score=0.75,
                verification_notes="Face verified successfully",
            )

        # Assert
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


# =============================================================================
# Test: Constants and configuration
# =============================================================================


class TestConstants:
    """Tests for service constants."""

    def test_similarity_threshold_is_valid(self):
        """Test that SIMILARITY_THRESHOLD is in valid range."""
        assert 0.0 <= SIMILARITY_THRESHOLD <= 1.0
        # The threshold is set to 0.35 (35%) for lenient matching
        assert SIMILARITY_THRESHOLD == 0.35


# =============================================================================
# Test: Edge cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_verify_face_with_invalid_image_data(self, service, mock_profile_repo, mock_db):
        """Test verification with corrupted/invalid image data."""
        from tests.conftest import create_mock_profile_row

        mock_profile = create_mock_profile_row()
        mock_profile_repo.get_by_employee_id.return_value = mock_profile

        # Invalid image data (not a valid image)
        invalid_data = b"not an image at all"

        result = service.verify_face(
            db=mock_db,
            employee_id="TEST001",
            selfie_image_data=invalid_data,
            selfie_mime="image/jpeg",
        )

        # Should return failure
        assert result["verified"] is False
        assert result["confidence_score"] == 0.0

    def test_verify_face_with_empty_image(self, service, mock_profile_repo, mock_db):
        """Test verification with empty image data."""
        from tests.conftest import create_mock_profile_row, create_test_image

        mock_profile = create_mock_profile_row()
        mock_profile_repo.get_by_employee_id.return_value = mock_profile

        with patch.object(
            service, "_download_image_from_storage", return_value=create_test_image()
        ):
            result = service.verify_face(
                db=mock_db, employee_id="TEST001", selfie_image_data=b"", selfie_mime="image/jpeg"
            )

        # Should return failure
        assert result["verified"] is False
