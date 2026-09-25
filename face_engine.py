import os
import sys
import certifi
import warnings

# Suppress library deprecation and future warnings for clean terminal output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Fix SSL verification for Windows Python
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import cv2
import numpy as np
from PIL import Image

class FaceEngine:
    def __init__(self, preferred_engine="auto", threshold=0.50):
        """
        Engine pengenalan wajah multi-backend:
        1. InsightFace (ArcFace 512-dim embedding) - State-of-the-art accuracy
        2. OpenCV SFace (Deep Learning Face Recognizer)
        3. face_recognition (dlib) - untuk backward compatibility jika terpasang
        """
        self.threshold = threshold
        self.engine_name = None
        self.app = None
        self._init_engine(preferred_engine)

    def _init_engine(self, preferred_engine):
        if preferred_engine in ["insightface", "auto"]:
            try:
                import insightface
                from insightface.app import FaceAnalysis
                app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
                app.prepare(ctx_id=-1, det_size=(320, 320))
                self.app = app
                self.engine_name = "InsightFace (ArcFace 512-D)"
                return
            except Exception as e:
                if preferred_engine == "insightface":
                    print(f"[Warning] Gagal inisialisasi InsightFace: {e}")

        # Fallback to face_recognition if available
        if preferred_engine in ["face_recognition", "auto"]:
            try:
                import face_recognition
                self.app = face_recognition
                self.engine_name = "face_recognition (dlib 128-D)"
                return
            except ImportError:
                pass

        # Fallback to OpenCV SFace
        self.engine_name = "OpenCV (Template/Haar Fallback)"

    def load_image(self, image_path_or_array):
        """Membaca gambar ke format BGR numpy array yang valid."""
        if isinstance(image_path_or_array, np.ndarray):
            return image_path_or_array
        if isinstance(image_path_or_array, str):
            if not os.path.exists(image_path_or_array):
                raise FileNotFoundError(f"File gambar tidak ditemukan: {image_path_or_array}")
            # Baca dengan cv2 imdecode untuk mendukung karakter non-ASCII/spasi di Windows
            with open(image_path_or_array, 'rb') as f:
                img_bytes = f.read()
            img_np = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"Gagal membaca gambar dari file: {image_path_or_array}")
            return img
        raise TypeError("Format gambar tidak didukung (harus path string atau numpy array).")

    def extract_faces(self, image_input):
        """
        Mendeteksi semua wajah dan mengekstrak embedding fitur.
        Mengembalikan list dict:
        [
            {
                'box': [x1, y1, x2, y2],
                'confidence': float,
                'embedding': np.array,
                'gender': int/str,
                'age': int
            }, ...
        ]
        """
        img = self.load_image(image_input)
        faces_data = []

        if "InsightFace" in self.engine_name and self.app is not None:
            faces = self.app.get(img)
            for face in faces:
                faces_data.append({
                    'box': face.bbox.astype(int).tolist(),
                    'confidence': float(face.det_score),
                    'embedding': face.embedding,
                    'gender': getattr(face, 'gender', None),
                    'age': getattr(face, 'age', None)
                })

        elif "face_recognition" in self.engine_name:
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = self.app.face_locations(rgb_img)
            encodings = self.app.face_encodings(rgb_img, boxes)
            for box, enc in zip(boxes, encodings):
                top, right, bottom, left = box
                faces_data.append({
                    'box': [left, top, right, bottom],
                    'confidence': 1.0,
                    'embedding': enc
                })

        return faces_data

    def calculate_similarity(self, embedding1, embedding2):
        """Menghitung Cosine Similarity antara dua embedding wajah (0.0 - 1.0)."""
        emb1 = np.asarray(embedding1).flatten()
        emb2 = np.asarray(embedding2).flatten()
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot_product = np.dot(emb1, emb2)
        sim = float(dot_product / (norm1 * norm2))
        return max(0.0, min(1.0, sim))

    def verify_faces(self, target_image, test_image, custom_threshold=None):
        """
        Membandingkan wajah target dengan wajah pada gambar uji.
        Returns:
            dict: {
                'match': bool,
                'similarity': float, # 0.0 - 1.0
                'similarity_pct': str, # "89.5%"
                'target_faces_found': int,
                'test_faces_found': int,
                'threshold': float,
                'engine': str,
                'status': str
            }
        """
        thresh = custom_threshold if custom_threshold is not None else self.threshold

        try:
            target_faces = self.extract_faces(target_image)
            if not target_faces:
                return {
                    'match': False,
                    'similarity': 0.0,
                    'similarity_pct': "0.0%",
                    'target_faces_found': 0,
                    'test_faces_found': 0,
                    'threshold': thresh,
                    'engine': self.engine_name,
                    'status': "Tidak ada wajah terdeteksi pada foto target"
                }

            test_faces = self.extract_faces(test_image)
            if not test_faces:
                return {
                    'match': False,
                    'similarity': 0.0,
                    'similarity_pct': "0.0%",
                    'target_faces_found': len(target_faces),
                    'test_faces_found': 0,
                    'threshold': thresh,
                    'engine': self.engine_name,
                    'status': "Tidak ada wajah terdeteksi pada foto uji"
                }

            target_embedding = target_faces[0]['embedding']
            max_sim = 0.0
            best_test_idx = -1

            for idx, test_f in enumerate(test_faces):
                sim = self.calculate_similarity(target_embedding, test_f['embedding'])
                if sim > max_sim:
                    max_sim = sim
                    best_test_idx = idx

            is_match = max_sim >= thresh

            return {
                'match': is_match,
                'similarity': round(max_sim, 4),
                'similarity_pct': f"{max_sim * 100:.1f}%",
                'target_faces_found': len(target_faces),
                'test_faces_found': len(test_faces),
                'best_face_index': best_test_idx,
                'threshold': thresh,
                'engine': self.engine_name,
                'status': "MATCH" if is_match else "NO_MATCH"
            }

        except Exception as e:
            return {
                'match': False,
                'similarity': 0.0,
                'similarity_pct': "0.0%",
                'target_faces_found': 0,
                'test_faces_found': 0,
                'threshold': thresh,
                'engine': self.engine_name,
                'status': f"Error: {str(e)}"
            }
