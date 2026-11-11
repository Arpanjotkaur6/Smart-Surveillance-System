
import cv2
from pathlib import Path


class FaceRecognizer:

    def __init__(self):

        model_path = (
            Path(__file__).resolve().parent
            / "face_recognition_sface_2021dec.onnx"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"SFace model not found: {model_path}"
            )

        self.recognizer = cv2.FaceRecognizerSF_create(
            str(model_path),
            ""
        )

    def get_embedding(self, frame, face):

        aligned_face = self.recognizer.alignCrop(
            frame,
            face
        )

        embedding = self.recognizer.feature(
            aligned_face
        )

        return embedding
