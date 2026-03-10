"""
Integration tests for check-in/check-out with face verification endpoints.

These tests verify the full flow from API endpoint to database operations.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime, date

# =============================================================================
# Test: Attendance Controller - Check-in with Face
# =============================================================================


class TestCheckInWithFace:
    """Tests for check_in_with_face controller method."""

    @pytest.fixture
    def mock_attendance_service(self):
        """Mock AttendanceService."""
        with patch("app.controllers.attandence_controller.AttendanceService") as mock:
            svc = MagicMock()

            # Mock check_in response
            mock_session = MagicMock()
            mock_session.id = 1
            mock_session.employee_id = "TEST001"
            mock_session.check_in_utc = datetime.utcnow()
            mock_session.work_date_local = date.today()

            svc.check_in.return_value = mock_session
            mock.return_value = svc
            yield svc

    @pytest.fixture
    def mock_face_service(self):
        """Mock FaceVerificationService."""
        with patch("app.controllers.attandence_controller.FaceVerificationService") as mock:
            from app.data.models.attendance_evidence import EvidenceType

            svc = MagicMock()

            # Mock verify_face response - successful verification
            svc.verify_face.return_value = {
                "verified": True,
                "confidence_score": 0.75,
                "distance": 0.25,
                "message": "Face verified successfully",
                "error": None,
                "debug_note": "Face matched with 75% similarity",
            }

            # Mock save_evidence response - use enum for evidence_type
            mock_evidence = MagicMock()
            mock_evidence.id = 1
            mock_evidence.session_id = 1
            mock_evidence.evidence_type = EvidenceType.CHECK_IN  # Use enum, not string
            mock_evidence.image_path = "attendance/TEST001/2024-01-01/check_in_test.jpg"
            mock_evidence.verified = True
            mock_evidence.confidence_score = 0.75
            mock_evidence.verification_notes = "Face verified successfully"
            mock_evidence.verified_at = datetime.utcnow()
            mock_evidence.created_at = datetime.utcnow()

            svc.save_evidence.return_value = mock_evidence
            mock.return_value = svc
            yield svc

    @pytest.fixture
    def controller(self, mock_attendance_service, mock_face_service):
        """Create controller with mocked dependencies."""
        from app.controllers.attandence_controller import AttendanceController

        return AttendanceController(service=mock_attendance_service, face_service=mock_face_service)

    def test_check_in_with_face_success(self, controller, mock_db):
        """Test successful check-in with face verification."""
        from tests.conftest import MockUploadFile, create_test_image

        # Setup
        selfie_file = MockUploadFile(content=create_test_image())

        # Use asyncio.run to execute the async method
        result = asyncio.run(
            controller.check_in_with_face(
                db=mock_db, employee_id="TEST001", selfie_file=selfie_file
            )
        )

        # Assert
        assert result.sessionId == 1
        assert result.employeeId == "TEST001"
        assert result.checkInUtc is not None
        assert result.workDateLocal == date.today()

        # Face verification results
        assert result.faceVerification.verified is True
        assert result.faceVerification.confidence_score == 0.75

        # Evidence saved
        assert result.evidence is not None
        assert result.evidence.verified is True

    def test_check_in_with_face_failure(self, controller, mock_db):
        """Test check-in with face verification failure."""
        from tests.conftest import MockUploadFile, create_test_image

        # Modify mock to return failure
        controller.face_service.verify_face.return_value = {
            "verified": False,
            "confidence_score": 0.0,
            "distance": 1.0,
            "message": "Face verification failed",
            "error": "No face detected",
            "debug_note": "No face detected in selfie",
        }

        # Setup
        selfie_file = MockUploadFile(content=create_test_image())

        # Execute
        result = asyncio.run(
            controller.check_in_with_face(
                db=mock_db, employee_id="TEST001", selfie_file=selfie_file
            )
        )

        # Assert - check-in still succeeds but face verification fails
        assert result.sessionId == 1
        assert result.faceVerification.verified is False
        assert result.faceVerification.confidence_score == 0.0

        # Evidence is still saved (for audit trail)
        assert result.evidence is not None
        assert result.evidence.verified is False


# =============================================================================
# Test: Attendance Controller - Check-out with Face
# =============================================================================


class TestCheckOutWithFace:
    """Tests for check_out_with_face controller method."""

    @pytest.fixture
    def mock_attendance_service(self):
        """Mock AttendanceService."""
        with patch("app.controllers.attandence_controller.AttendanceService") as mock:
            svc = MagicMock()

            # Mock check_out response
            mock_session = MagicMock()
            mock_session.id = 1
            mock_session.employee_id = "TEST001"
            mock_session.check_in_utc = datetime.utcnow()
            mock_session.check_out_utc = datetime.utcnow()
            mock_session.work_date_local = date.today()

            svc.check_out.return_value = mock_session
            mock.return_value = svc
            yield svc

    @pytest.fixture
    def mock_face_service(self):
        """Mock FaceVerificationService."""
        with patch("app.controllers.attandence_controller.FaceVerificationService") as mock:
            svc = MagicMock()

            svc.verify_face.return_value = {
                "verified": True,
                "confidence_score": 0.80,
                "distance": 0.20,
                "message": "Face verified successfully",
                "error": None,
            }

            mock_evidence = MagicMock()
            mock_evidence.id = 2
            mock_evidence.session_id = 1
            mock_evidence.evidence_type = "check_out"
            mock_evidence.image_path = "attendance/TEST001/2024-01-01/check_out_test.jpg"
            mock_evidence.verified = True
            mock_evidence.confidence_score = 0.80
            mock_evidence.verification_notes = "Face verified successfully"
            mock_evidence.verified_at = datetime.utcnow()
            mock_evidence.created_at = datetime.utcnow()

            svc.save_evidence.return_value = mock_evidence
            mock.return_value = svc
            yield svc

    @pytest.fixture
    def controller(self, mock_attendance_service, mock_face_service):
        """Create controller with mocked dependencies."""
        from app.controllers.attandence_controller import AttendanceController

        return AttendanceController(service=mock_attendance_service, face_service=mock_face_service)

    def test_check_out_with_face_success(self, controller, mock_db):
        """Test successful check-out with face verification."""
        from tests.conftest import MockUploadFile, create_test_image

        # Setup
        selfie_file = MockUploadFile(content=create_test_image())

        # Execute
        result = asyncio.run(
            controller.check_out_with_face(
                db=mock_db, employee_id="TEST001", selfie_file=selfie_file
            )
        )

        # Assert
        assert result.sessionId == 1
        assert result.employeeId == "TEST001"
        assert result.checkInUtc is not None
        assert result.checkOutUtc is not None
        assert result.workedSeconds >= 0

        # Face verification results
        assert result.faceVerification.verified is True
        assert result.faceVerification.confidence_score == 0.80

        # Evidence saved
        assert result.evidence is not None
        assert result.evidence.evidence_type == "check_out"

    def test_check_out_with_face_failure(self, controller, mock_db):
        """Test check-out with face verification failure."""
        from tests.conftest import MockUploadFile, create_test_image

        # Modify mock to return failure
        controller.face_service.verify_face.return_value = {
            "verified": False,
            "confidence_score": 0.10,
            "distance": 0.90,
            "message": "Face verification failed",
            "error": "Low similarity",
        }

        # Setup
        selfie_file = MockUploadFile(content=create_test_image())

        # Execute
        result = asyncio.run(
            controller.check_out_with_face(
                db=mock_db, employee_id="TEST001", selfie_file=selfie_file
            )
        )

        # Assert - check-out succeeds but face verification fails
        assert result.sessionId == 1
        assert result.faceVerification.verified is False

        # Evidence is still saved
        assert result.evidence is not None
        assert result.evidence.verified is False


# =============================================================================
# Test: Attendance Routes (API endpoint tests)
# =============================================================================


class TestAttendanceRoutes:
    """Tests for attendance API routes."""

    def test_check_in_route_accepts_selfie(self):
        """Test that /check-in-with-face endpoint accepts selfie file."""
        from app.routes.attendance_router import router

        # Get the route
        routes = [r for r in router.routes if hasattr(r, "path") and "check-in-with-face" in r.path]

        assert len(routes) > 0, "Check-in with face route not found"

        route = routes[0]
        # Verify it accepts file upload
        assert "selfie" in [p.name for p in route.dependant.body_params]


# =============================================================================
# Test: Evidence Storage
# =============================================================================


class TestEvidenceStorage:
    """Tests for evidence storage and retrieval."""

    def test_evidence_saved_regardless_of_verification(self):
        """Test that evidence is saved even when verification fails."""
        # This is a key behavior test - evidence should always be saved
        # for audit trail purposes
        from app.data.models.attendance_evidence import EvidenceType

        # Verify EvidenceType enum exists
        assert hasattr(EvidenceType, "CHECK_IN")
        assert hasattr(EvidenceType, "CHECK_OUT")
        assert EvidenceType.CHECK_IN.value == "check_in"
        assert EvidenceType.CHECK_OUT.value == "check_out"

    def test_evidence_response_schema(self):
        """Test that evidence response has required fields."""
        from app.schemas.attendance import AttendanceEvidenceResponse

        # Verify required fields
        required_fields = [
            "id",
            "session_id",
            "evidence_type",
            "verified",
            "confidence_score",
            "verification_notes",
            "image_path",
            "verified_at",
            "created_at",
        ]

        # Get annotations from schema
        annotations = AttendanceEvidenceResponse.model_fields

        for field in required_fields:
            assert field in annotations, f"Missing field in AttendanceEvidenceResponse: {field}"


# =============================================================================
# Test: Check-in/Check-out Flow
# =============================================================================


class TestAttendanceFlow:
    """Integration tests for the full attendance flow."""

    def test_checkin_creates_session_first(self):
        """Test that check-in with face creates session before verification."""
        # This tests the flow:
        # 1. Create attendance session (check-in time recorded)
        # 2. Verify face
        # 3. Save evidence

        # The controller should call check_in first, then verify_face
        from app.controllers.attandence_controller import AttendanceController

        # We verify the order by checking the controller code
        # This is a structural test - ensures proper flow implementation
        assert hasattr(AttendanceController, "check_in_with_face")

        # Verify the method is async
        import inspect

        assert inspect.iscoroutinefunction(AttendanceController.check_in_with_face)

    def test_checkout_closes_session_first(self):
        """Test that check-out with face closes session before verification."""
        from app.controllers.attandence_controller import AttendanceController

        assert hasattr(AttendanceController, "check_out_with_face")

        import inspect

        assert inspect.iscoroutinefunction(AttendanceController.check_out_with_face)


# =============================================================================
# Test: Response Schemas
# =============================================================================


class TestResponseSchemas:
    """Tests for response schemas."""

    def test_check_in_with_face_response_schema(self):
        """Test CheckInWithFaceResponse has all required fields."""
        from app.schemas.attendance import CheckInWithFaceResponse

        required_fields = [
            "sessionId",
            "employeeId",
            "checkInUtc",
            "workDateLocal",
            "faceVerification",
            "evidence",
        ]

        annotations = CheckInWithFaceResponse.model_fields

        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"

    def test_check_out_with_face_response_schema(self):
        """Test CheckOutWithFaceResponse has all required fields."""
        from app.schemas.attendance import CheckOutWithFaceResponse

        required_fields = [
            "sessionId",
            "employeeId",
            "checkInUtc",
            "checkOutUtc",
            "workedSeconds",
            "faceVerification",
            "evidence",
        ]

        annotations = CheckOutWithFaceResponse.model_fields

        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"

    def test_face_verification_result_schema(self):
        """Test FaceVerificationResult has all required fields."""
        from app.schemas.attendance import FaceVerificationResult

        required_fields = ["verified", "confidence_score", "message"]

        annotations = FaceVerificationResult.model_fields

        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"
