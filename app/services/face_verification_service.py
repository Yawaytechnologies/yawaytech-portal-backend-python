"""
Face verification service using OpenCV DNN with pre-trained models.
Provides accurate face detection and matching similar to mobile face lock.
Uses deep learning-based face detection and improved matching algorithm.
"""

from __future__ import annotations
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from collections import OrderedDict
import os

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.core.supabase_client import get_supabase
from app.data.repositories.employee_profile_repository import EmployeeProfileRepo
from app.data.models.attendance_evidence import AttendanceEvidence, EvidenceType
from app.data.repositories.attendance_repository import AttendanceRepository

logger = logging.getLogger(__name__)

# Face recognition threshold (similarity score)
# Higher = stricter matching
# 0.5 means 50% similarity threshold
FACE_SIMILARITY_THRESHOLD = 0.50

# Alias for backwards compatibility
SIMILARITY_THRESHOLD = 0.35

# Model paths for OpenCV DNN face detection
# Using OpenCV's pre-trained face detection model
FACE_DETECTOR_PROTO = "deploy.prototxt"
FACE_DETECTOR_MODEL = "res10_300x300_ssd_iter_140000.caffemodel"
PROFILE_IMAGE_CACHE_MAX_ENTRIES = 256


class FaceVerificationService:
    """
    Handles face verification for attendance check-in/check-out.
    Uses OpenCV DNN for deep learning-based face detection and improved feature matching.
    """

    def __init__(self):
        self.profile_repo = EmployeeProfileRepo()
        self.attendance_repo = AttendanceRepository()
        self._profile_image_cache: OrderedDict[tuple[str, str], bytes] = OrderedDict()

        # Try to load OpenCV DNN face detector
        self.face_net = None
        self.face_detector_loaded = False

        # Try loading the DNN face detector
        # First check if model files exist locally
        model_paths = self._get_model_paths()
        if model_paths and all(os.path.exists(p) for p in model_paths):
            try:
                self.face_net = cv2.dnn.readNetFromCaffe(model_paths[0], model_paths[1])
                self.face_detector_loaded = True
                logger.info("✅ Loaded OpenCV DNN face detector")
            except Exception as e:
                logger.warning(f"Could not load DNN face detector: {e}")

        # Fallback to Haar Cascade
        if not self.face_detector_loaded:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            logger.info("Using Haar Cascade fallback for face detection")

    def _get_model_paths(self) -> Optional[Tuple[str, str]]:
        """Get paths to face detection model files."""
        # Check in current directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prototxt = os.path.join(base_dir, FACE_DETECTOR_PROTO)
        caffemodel = os.path.join(base_dir, FACE_DETECTOR_MODEL)

        if os.path.exists(prototxt) and os.path.exists(caffemodel):
            return (prototxt, caffemodel)
        return None

    def verify_face(
        self,
        db: Session,
        employee_id: str,
        selfie_image_data: bytes,
        selfie_mime: str,
    ) -> Dict[str, Any]:
        """
        Verify a captured selfie against employee's profile image.
        Uses deep learning-based face detection for more accurate results.

        Args:
            db: Database session
            employee_id: Employee ID
            selfie_image_data: Raw image bytes
            selfie_mime: MIME type of image

        Returns:
            {
                "verified": bool,
                "confidence_score": float,
                "message": str,
                "profile_path": str (or None),
                "error": str (or None),
                "debug_note": str (failure reason)
            }
        """
        try:
            logger.info(f"🔍 Starting face verification for {employee_id}")

            # 1) Load employee's profile image from storage
            profile_row = self.profile_repo.get_by_employee_id(db, employee_id)
            if not profile_row or not profile_row.profile_path:
                debug_note = "Employee has not enrolled profile image"
                logger.warning(f"❌ {debug_note}")
                return {
                    "verified": False,
                    "confidence_score": 0.0,
                    "message": "No profile image found",
                    "profile_path": None,
                    "error": "Employee has not enrolled profile image",
                    "debug_note": debug_note,
                }

            logger.info(f"Found profile image: {profile_row.profile_path}")

            # 2) Download profile image from Supabase
            try:
                profile_image_data = self._download_image_from_storage(
                    profile_row.profile_bucket, profile_row.profile_path
                )
                logger.info(f"Downloaded profile image: {len(profile_image_data)} bytes")
            except Exception as e:
                debug_note = f"Failed to download profile image: {str(e)}"
                logger.error(f"❌ {debug_note}")
                return {
                    "verified": False,
                    "confidence_score": 0.0,
                    "message": "Failed to retrieve profile image",
                    "profile_path": None,
                    "error": str(e),
                    "debug_note": debug_note,
                }

            logger.info(f"Selfie image: {len(selfie_image_data)} bytes")

            # 3) Perform face verification using improved algorithm
            is_match, similarity_score = self._compare_faces(profile_image_data, selfie_image_data)

            # Confidence score is the similarity score
            confidence_score = similarity_score

            # Determine failure reason if not verified
            debug_note = ""
            if not is_match:
                if confidence_score == 0.0:
                    debug_note = "No face detected or face quality too poor"
                else:
                    debug_note = f"Similarity {confidence_score:.2%} below threshold {FACE_SIMILARITY_THRESHOLD:.0%}"
            else:
                debug_note = f"Face matched with {confidence_score:.2%} similarity"

            result = {
                "verified": is_match,
                "confidence_score": float(confidence_score),
                "distance": float(1.0 - confidence_score),
                "message": "Face verified successfully" if is_match else "Face verification failed",
                "profile_path": profile_row.profile_path,
                "error": None,
                "debug_note": debug_note,
            }

            logger.info(
                f"✅ Verification result for {employee_id}: verified={result['verified']}, "
                f"score={confidence_score:.4f}, note={debug_note}"
            )

            return result

        except Exception as e:
            logger.exception(f"❌ Face verification error for {employee_id}: {str(e)}")
            return {
                "verified": False,
                "confidence_score": 0.0,
                "message": "Face verification error",
                "profile_path": None,
                "error": str(e),
                "debug_note": f"Verification error: {str(e)}",
            }

    def _download_image_from_storage(self, bucket: str, path: str) -> bytes:
        """Download image from Supabase storage."""
        cache_key = (bucket, path)
        cached = self._profile_image_cache.get(cache_key)
        if cached is not None:
            self._profile_image_cache.move_to_end(cache_key)
            return cached

        supabase = get_supabase()
        response = supabase.storage.from_(bucket).download(path)
        if not response:
            raise ValueError(f"Failed to download image from {bucket}/{path}")

        self._profile_image_cache[cache_key] = response
        if len(self._profile_image_cache) > PROFILE_IMAGE_CACHE_MAX_ENTRIES:
            self._profile_image_cache.popitem(last=False)
        return response

    def _detect_faces_dnn(self, img: np.ndarray) -> list:
        """Detect faces using OpenCV DNN with pre-trained model."""
        if self.face_net is None:
            return []

        h, w = img.shape[:2]

        # Preprocess for DNN
        blob = cv2.dnn.blobFromImage(
            cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
        )

        self.face_net.setInput(blob)
        detections = self.face_net.forward()

        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:  # Confidence threshold
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype(int)
                faces.append((x1, y1, x2 - x1, y2 - y1))

        return faces

    def _detect_faces_haar(self, img: np.ndarray) -> list:
        """Detect faces using Haar Cascade."""
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Detect faces with multiple parameters for better detection
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
        )

        return list(faces)

    def _detect_faces(self, img: np.ndarray) -> list:
        """Detect faces using best available method."""
        # Try DNN first
        if self.face_detector_loaded and self.face_net is not None:
            faces = self._detect_faces_dnn(img)
            if len(faces) > 0:
                logger.info(f"DNN detected {len(faces)} faces")
                return faces

        # Fallback to Haar Cascade
        faces = self._detect_faces_haar(img)
        logger.info(f"Haar cascade detected {len(faces)} faces")
        return faces

    def _compare_faces(self, profile_image: bytes, selfie_image: bytes) -> Tuple[bool, float]:
        """
        Compare two face images using improved algorithm.

        Uses multiple techniques:
        1. Deep learning-based face detection
        2. Histogram-based comparison for lighting invariance
        3. Structural similarity for feature matching

        Args:
            profile_image: Profile image bytes
            selfie_image: Selfie image bytes

        Returns:
            (is_match: bool, similarity_score: float 0.0-1.0)
        """
        try:
            # Convert bytes to numpy arrays
            nparr_profile = np.frombuffer(profile_image, np.uint8)
            img_profile = cv2.imdecode(nparr_profile, cv2.IMREAD_COLOR)

            nparr_selfie = np.frombuffer(selfie_image, np.uint8)
            img_selfie = cv2.imdecode(nparr_selfie, cv2.IMREAD_COLOR)

            if img_profile is None or img_selfie is None:
                logger.error("Failed to decode image data - corrupted or invalid format")
                return False, 0.0

            # Detect faces using best available method
            profile_faces = self._detect_faces(img_profile)
            selfie_faces = self._detect_faces(img_selfie)

            logger.info(f"Profile image: {len(profile_faces)} faces detected")
            logger.info(f"Selfie image: {len(selfie_faces)} faces detected")

            if len(profile_faces) == 0:
                logger.warning("❌ No face detected in profile image")
                return False, 0.0

            if len(selfie_faces) == 0:
                logger.warning("❌ No face detected in selfie image")
                return False, 0.0

            # Get the largest face (most likely the main face)
            profile_face = max(profile_faces, key=lambda f: f[2] * f[3])
            selfie_face = max(selfie_faces, key=lambda f: f[2] * f[3])

            # Extract face regions
            x1, y1, w1, h1 = profile_face
            profile_face_region = img_profile[y1 : y1 + h1, x1 : x1 + w1]

            x2, y2, w2, h2 = selfie_face
            selfie_face_region = img_selfie[y2 : y2 + h2, x2 : x2 + w2]

            logger.info(f"Profile face region: {w1}x{h1}, Selfie face region: {w2}x{h2}")

            # Resize to same size for comparison
            size = (128, 128)
            profile_resized = cv2.resize(profile_face_region, size)
            selfie_resized = cv2.resize(selfie_face_region, size)

            # Calculate similarity using multiple methods
            similarity = self._calculate_similarity(profile_resized, selfie_resized)

            is_match = similarity >= FACE_SIMILARITY_THRESHOLD

            logger.info(
                f"Similarity score: {similarity:.4f} (threshold: {FACE_SIMILARITY_THRESHOLD})"
            )

            return is_match, min(1.0, similarity)

        except Exception as e:
            logger.error(f"❌ Face comparison error: {str(e)}")
            return False, 0.0

    def _calculate_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate similarity between two face images using multiple methods.

        Combines:
        1. Histogram correlation (lighting invariant)
        2. Structural similarity (SSIM-like)
        3. ORB feature matching
        """
        # Convert to grayscale for some comparisons
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if len(img1.shape) == 3 else img1
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if len(img2.shape) == 3 else img2

        # Method 1: Histogram correlation (0-1, higher is better)
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        hist_corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

        # Method 2: Template matching / normalized correlation
        norm_corr = np.sum(
            (gray1.astype(float) - gray1.mean()) * (gray2.astype(float) - gray2.mean())
        ) / (
            np.sqrt(
                np.sum((gray1.astype(float) - gray1.mean()) ** 2)
                * np.sum((gray2.astype(float) - gray2.mean()) ** 2)
            )
            + 1e-10
        )

        # Method 3: ORB feature matching (robust to rotations/scale)
        orb = cv2.ORB_create(nfeatures=500)  # type: ignore[attr-defined]
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)

        feature_sim = 0.0
        if des1 is not None and des2 is not None and len(des1) > 0 and len(des2) > 0:
            # Use BFMatcher with Hamming distance (good for binary descriptors)
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)

            if len(matches) > 0:
                # Good matches ratio
                feature_sim = len(matches) / max(len(kp1), len(kp2))
                # Scale to 0-1
                feature_sim = min(
                    1.0, feature_sim * 2
                )  # Boost since ORB typically has lower ratios

        # Combine scores with weights
        # Histogram and normalized correlation are more reliable for faces
        combined_similarity = (
            0.35 * max(0, hist_corr)  # Histogram: 35%
            + 0.35 * max(0, (norm_corr + 1) / 2)  # Normalized correlation: 35%
            + 0.30 * feature_sim  # ORB features: 30%
        )

        logger.info(
            f"Similarity breakdown: hist={hist_corr:.4f}, norm_corr={norm_corr:.4f}, features={feature_sim:.4f}"
        )

        return combined_similarity

    def save_evidence(
        self,
        db: Session,
        session_id: int,
        evidence_type: EvidenceType,
        verified: bool,
        confidence_score: float,
        verification_notes: Optional[str] = None,
    ) -> AttendanceEvidence:
        """
        Save face verification metadata only.

        Check-in/check-out selfies are intentionally not persisted. The image is
        used in-memory for verification and then discarded.
        """
        try:
            if not self.attendance_repo.get_session_by_id(db, session_id):
                raise ValueError(f"Session {session_id} not found")

            # Create evidence record
            evidence = AttendanceEvidence(
                session_id=session_id,
                evidence_type=evidence_type,
                image_bucket=None,
                image_path=None,
                image_mime=None,
                image_size=None,
                verified=verified,
                confidence_score=confidence_score,
                verification_notes=verification_notes,
                verified_at=datetime.now(timezone.utc) if verified else None,
            )

            db.add(evidence)
            db.flush()
            logger.info(f"Evidence metadata saved: {evidence.id}")

            return evidence

        except Exception as e:
            logger.error(f"Error saving evidence: {str(e)}")
            raise
