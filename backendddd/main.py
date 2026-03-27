"""
Kids Monitoring System - Face Recognition
==========================================
Uses InsightFace (buffalo_l model with ArcFace) for face detection and recognition.
Stores face embeddings in MongoDB (kids_face_data.face_embeddings).

Modes:
  1. Register new face (provide image path + name)
  2. Live webcam detection
  3. Detect from video file
  4. Detect from image file
  5. List registered faces
  6. Delete a registered face
  0. Exit
"""

import os
import sys
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from pymongo import MongoClient
from datetime import datetime


# ─── Configuration ───────────────────────────────────────────────────────────

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "kids_face_data"
COLLECTION_NAME = "face_embeddings"
COSINE_SIMILARITY_THRESHOLD = 0.5  # Faces with similarity >= this are considered a match
MODEL_NAME = "buffalo_l"           # InsightFace model pack (includes ArcFace)


# ─── MongoDB Helper ──────────────────────────────────────────────────────────

class FaceDatabase:
    """Handles storing and retrieving face embeddings from MongoDB."""

    def __init__(self, uri: str = MONGO_URI, db_name: str = DB_NAME, collection: str = COLLECTION_NAME):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection]
        print(f"[INFO] Connected to MongoDB: {db_name}.{collection}")

    def add_face(self, name: str, embedding: np.ndarray) -> bool:
        """Store a face embedding with the given name."""
        doc = {
            "name": name,
            "embedding": embedding.tolist(),
            "registered_at": datetime.utcnow().isoformat()
        }
        result = self.collection.insert_one(doc)
        return result.acknowledged

    def get_all_faces(self) -> list:
        """Retrieve all registered faces as list of (name, embedding) tuples."""
        faces = []
        for doc in self.collection.find({}, {"name": 1, "embedding": 1}):
            name = doc["name"]
            embedding = np.array(doc["embedding"], dtype=np.float32)
            faces.append((name, embedding))
        return faces

    def list_names(self) -> list:
        """Return a list of all registered names."""
        return self.collection.distinct("name")

    def delete_face(self, name: str) -> int:
        """Delete all embeddings for a given name. Returns count of deleted docs."""
        result = self.collection.delete_many({"name": name})
        return result.deleted_count

    def count(self) -> int:
        """Return total number of registered face embeddings."""
        return self.collection.count_documents({})


# ─── Face Recognition Engine ─────────────────────────────────────────────────

class FaceRecognitionEngine:
    """Wraps InsightFace for detection + ArcFace recognition."""

    def __init__(self, model_name: str = MODEL_NAME):
        print(f"[INFO] Loading InsightFace model: {model_name} ...")
        self.app = FaceAnalysis(name=model_name, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        print("[INFO] InsightFace model loaded successfully.")

    def get_faces(self, image: np.ndarray) -> list:
        """
        Detect faces in an image.
        Returns list of insightface Face objects (each has .embedding, .bbox, etc.)
        """
        faces = self.app.get(image)
        return faces

    def get_embedding(self, image: np.ndarray) -> np.ndarray | None:
        """
        Get the embedding of the largest/first detected face in the image.
        Returns None if no face is found.
        """
        faces = self.get_faces(image)
        if not faces:
            return None
        # Pick the face with the largest bounding box area (most prominent)
        best_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        return best_face.embedding

    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        dot = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot / (norm1 * norm2))


# ─── Recognition Logic ───────────────────────────────────────────────────────

def identify_face(embedding: np.ndarray, known_faces: list, threshold: float = COSINE_SIMILARITY_THRESHOLD) -> tuple:
    """
    Compare an embedding against known faces.
    Returns (name, similarity) of the best match, or ("Unknown", 0.0) if no match.
    """
    best_name = "Unknown"
    best_score = 0.0

    for name, known_emb in known_faces:
        score = FaceRecognitionEngine.cosine_similarity(embedding, known_emb)
        if score > best_score:
            best_score = score
            best_name = name

    if best_score >= threshold:
        return best_name, best_score
    return "Unknown", best_score


def draw_results(frame: np.ndarray, faces: list, known_faces: list, threshold: float = COSINE_SIMILARITY_THRESHOLD) -> np.ndarray:
    """
    Draw bounding boxes and names on the frame for each detected face.
    """
    for face in faces:
        bbox = face.bbox.astype(int)
        x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]

        embedding = face.embedding
        name, score = identify_face(embedding, known_faces, threshold)

        # Color: green for known, red for unknown
        if name != "Unknown":
            color = (0, 255, 0)
            label = f"{name} ({score:.2f})"
        else:
            color = (0, 0, 255) 
            label = f"Unknown ({score:.2f})"

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Draw label background
        label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return frame


# ─── Menu Actions ─────────────────────────────────────────────────────────────

def register_face(engine: FaceRecognitionEngine, db: FaceDatabase):
    """Register a new face from an image file."""
    print("\n--- Register New Face ---")
    image_path = input("Enter the image file path: ").strip().strip('"').strip("'")

    if not os.path.isfile(image_path):
        print(f"[ERROR] File not found: {image_path}")
        return

    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Could not read image: {image_path}")
        return

    print("[INFO] Detecting face in the image...")
    embedding = engine.get_embedding(image)

    if embedding is None:
        print("[ERROR] No face detected in the image. Please try another image.")
        return

    name = input("Enter the person's name: ").strip()
    if not name:
        print("[ERROR] Name cannot be empty.")
        return

    if db.add_face(name, embedding):
        print(f"[SUCCESS] Face registered for '{name}' successfully!")
        print(f"[INFO] Total registered faces: {db.count()}")
    else:
        print("[ERROR] Failed to save face to database.")


def live_webcam_detection(engine: FaceRecognitionEngine, db: FaceDatabase):
    """Run live face detection and recognition from webcam."""
    print("\n--- Live Webcam Detection ---")
    known_faces = db.get_all_faces()
    print(f"[INFO] Loaded {len(known_faces)} registered face(s) from database.")

    if not known_faces:
        print("[WARNING] No faces registered yet. All faces will show as 'Unknown'.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    print("[INFO] Press 'q' to quit webcam detection.")
    print("[INFO] Press 's' to take a screenshot.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame from webcam.")
            break

        # Detect faces
        faces = engine.get_faces(frame)

        # Draw results
        frame = draw_results(frame, faces, known_faces)

        # Show info overlay
        info_text = f"Faces: {len(faces)} | Registered: {len(known_faces)} | Press 'q' to quit"
        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Kids Monitoring - Live Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            screenshot_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(screenshot_name, frame)
            print(f"[INFO] Screenshot saved: {screenshot_name}")

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Webcam detection stopped.")


def detect_from_video(engine: FaceRecognitionEngine, db: FaceDatabase):
    """Detect and recognize faces from a video file."""
    print("\n--- Detect from Video File ---")
    video_path = input("Enter the video file path: ").strip().strip('"').strip("'")

    if not os.path.isfile(video_path):
        print(f"[ERROR] File not found: {video_path}")
        return

    known_faces = db.get_all_faces()
    print(f"[INFO] Loaded {len(known_faces)} registered face(s) from database.")

    if not known_faces:
        print("[WARNING] No faces registered yet. All faces will show as 'Unknown'.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[INFO] Video: {fps:.1f} FPS, {total_frames} frames")
    print("[INFO] Press 'q' to quit, 'p' to pause/resume.")

    paused = False
    frame_count = 0

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("[INFO] End of video reached.")
                break
            frame_count += 1

            # Detect faces
            faces = engine.get_faces(frame)

            # Draw results
            frame = draw_results(frame, faces, known_faces)

            # Show info overlay
            progress = f"Frame: {frame_count}/{total_frames}"
            info_text = f"Faces: {len(faces)} | {progress} | Press 'q' to quit"
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.imshow("Kids Monitoring - Video Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
            state = "PAUSED" if paused else "PLAYING"
            print(f"[INFO] Video {state}")

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Video detection stopped.")


def detect_from_image(engine: FaceRecognitionEngine, db: FaceDatabase):
    """Detect and recognize faces from an image file."""
    print("\n--- Detect from Image File ---")
    image_path = input("Enter the image file path: ").strip().strip('"').strip("'")

    if not os.path.isfile(image_path):
        print(f"[ERROR] File not found: {image_path}")
        return

    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Could not read image: {image_path}")
        return

    known_faces = db.get_all_faces()
    print(f"[INFO] Loaded {len(known_faces)} registered face(s) from database.")

    if not known_faces:
        print("[WARNING] No faces registered yet. All faces will show as 'Unknown'.")

    # Detect faces
    faces = engine.get_faces(image)
    print(f"[INFO] Detected {len(faces)} face(s) in the image.")

    if not faces:
        print("[INFO] No faces detected in the image.")
        return

    # Draw results
    result_image = draw_results(image.copy(), faces, known_faces)

    # Print results to console
    for i, face in enumerate(faces):
        name, score = identify_face(face.embedding, known_faces)
        bbox = face.bbox.astype(int)
        print(f"  Face {i+1}: {name} (similarity: {score:.4f}) | BBox: ({bbox[0]}, {bbox[1]}) - ({bbox[2]}, {bbox[3]})")

    # Show result
    cv2.imshow("Kids Monitoring - Image Detection", result_image)
    print("[INFO] Press any key to close the image window.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Optionally save result
    save = input("Save result image? (y/n): ").strip().lower()
    if save == 'y':
        output_path = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(output_path, result_image)
        print(f"[INFO] Result saved: {output_path}")


def list_registered_faces(db: FaceDatabase):
    """List all registered face names."""
    print("\n--- Registered Faces ---")
    names = db.list_names()
    if not names:
        print("[INFO] No faces registered yet.")
        return
    print(f"[INFO] Total unique names: {len(names)}")
    for i, name in enumerate(names, 1):
        count = db.collection.count_documents({"name": name})
        print(f"  {i}. {name} ({count} embedding(s))")


def delete_registered_face(db: FaceDatabase):
    """Delete a registered face by name."""
    print("\n--- Delete Registered Face ---")
    names = db.list_names()
    if not names:
        print("[INFO] No faces registered yet.")
        return

    print("Registered names:")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")

    name_input = input("Enter the name to delete (or number): ").strip()

    # Allow selection by number
    try:
        idx = int(name_input) - 1
        if 0 <= idx < len(names):
            name_input = names[idx]
    except ValueError:
        pass

    confirm = input(f"Are you sure you want to delete all embeddings for '{name_input}'? (y/n): ").strip().lower()
    if confirm == 'y':
        deleted = db.delete_face(name_input)
        if deleted > 0:
            print(f"[SUCCESS] Deleted {deleted} embedding(s) for '{name_input}'.")
        else:
            print(f"[INFO] No embeddings found for '{name_input}'.")
    else:
        print("[INFO] Deletion cancelled.")


# ─── Main Menu ────────────────────────────────────────────────────────────────

def print_menu():
    """Display the main menu."""
    print("\n" + "=" * 50)
    print("   Kids Monitoring System - Face Recognition")
    print("=" * 50)
    print("  1. Register new face (from image)")
    print("  2. Live webcam detection")
    print("  3. Detect from video file")
    print("  4. Detect from image file")
    print("  5. List registered faces")
    print("  6. Delete a registered face")
    print("  0. Exit")
    print("=" * 50)


def main():
    """Main entry point."""
    print("[INFO] Initializing Kids Monitoring System...")

    # Initialize MongoDB connection
    try:
        db = FaceDatabase()
    except Exception as e:
        print(f"[ERROR] Could not connect to MongoDB: {e}")
        print("[HINT] Make sure MongoDB is running on localhost:27017")
        sys.exit(1)

    # Initialize InsightFace engine
    try:
        engine = FaceRecognitionEngine()
    except Exception as e:
        print(f"[ERROR] Could not load InsightFace model: {e}")
        print("[HINT] Make sure insightface and onnxruntime are installed correctly.")
        sys.exit(1)

    print(f"[INFO] System ready. {db.count()} face(s) registered in database.")

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        if choice == '1':
            register_face(engine, db)
        elif choice == '2':
            live_webcam_detection(engine, db)
        elif choice == '3':
            detect_from_video(engine, db)
        elif choice == '4':
            detect_from_image(engine, db)
        elif choice == '5':
            list_registered_faces(db)
        elif choice == '6':
            delete_registered_face(db)
        elif choice == '0':
            print("[INFO] Exiting Kids Monitoring System. Goodbye!")
            break
        else:
            print("[ERROR] Invalid option. Please try again.")


if __name__ == "__main__":
    main()
