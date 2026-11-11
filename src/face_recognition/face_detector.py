
import cv2
from pathlib import Path


class FaceDetector:

    def __init__(self, score_threshold=0.7):

        model_path = (
            Path(__file__).resolve().parent
            / "face_detection_yunet_2023mar.onnx"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"YuNet model not found: {model_path}"
            )

        self.detector = cv2.FaceDetectorYN_create(
            str(model_path),
            "",
            (320, 320),
            score_threshold,
            0.3,
            5000
        )

    def detect(self, frame):

        height, width = frame.shape[:2]

        self.detector.setInputSize((width, height))

        _, faces = self.detector.detect(frame)

        return faces
