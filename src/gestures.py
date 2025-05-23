import numpy as np
import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import Frame, Button, Label, Canvas, Scrollbar
from PIL import Image, ImageTk
import threading
import time
import os
import math

# Initialize MediaPipe hands and drawing utilities
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Initialize Mediapipe face and drawing utilities
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Function to recognize basic gestures
def recognize_gesture(hand_landmarks):
    thumb_up = False
    index_up = False
    middle_up = False

    # Extract landmarks
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

    # Check thumb position
    if thumb_tip.y < wrist.y:
        thumb_up = True
    
    # Check index and middle finger positions
    if index_tip.y < wrist.y:
        index_up = True
    if middle_tip.y < wrist.y:
        middle_up = True

    # Classify gestures
    if thumb_up and not index_up and not middle_up:
        return "Thumbs Up"
    elif index_up and middle_up and not thumb_up:
        return "Peace Sign"
    elif not thumb_up and not index_up and not middle_up:
        return "Fist"
    elif thumb_up and index_up and middle_up:
        return "Open Hand"
    else:
        return "Unknown Gesture"

def get_centroid(box):
    x, y, w, h = box
    return x + w // 2, y + h // 2

def euclidean_distance(pt1, pt2):
    return math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)

def associate_hands(hand_centroids, face_centroids, threshold):
    hand_face_associations = []
    for hand in hand_centroids:
        closest_face = None
        min_distance = float('inf')
        for face in face_centroids:
            distance = euclidean_distance(hand, face)
            if distance < min_distance and distance < threshold:
                min_distance = distance
                closest_face = face
        if closest_face:
            hand_face_associations.append((hand, closest_face))
    return hand_face_associations


class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Photo App")
        self.root.geometry("800x500")
        self.face_count = 0
        self.face_count_var = tk.StringVar()

        # Video capture and processing
        self.cap = cv2.VideoCapture(0)
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.size = (640, 360)

        # Flags and data
        self.running = True
        self.current_frame = None  # Store the current frame for capturing
        self.photo_paths = []  # List to store captured photos
        self.displaying_image = False  # Tracks whether to display the video feed

        # Create UI elements
        self.create_widgets()

        # Start video processing in a separate thread
        self.video_thread = threading.Thread(target=self.process_video)
        self.video_thread.daemon = True
        self.video_thread.start()

    def create_widgets(self):
        # Colors
        background = "#ee0b0b"
        background_light = "#0bee3f"
        button_color = "#717af0"
        button_fg = "black"

        # Header
        header_frame = Frame(self.root, height=50, bg=background)
        header_frame.pack(side="top", fill="x")

        Label(
            header_frame,
            text="Auto Photo App",
            font=("Helvetica", 18, "bold"),
            bg=background,
            fg="white",
        ).pack(side="left", padx=20)

        # Face Count Label

        self.face_count_var.set(f"Faces Detected: {self.face_count}")
        face_count_label = Label(root, textvariable=self.face_count_var, font=("Arial", 16))
        face_count_label.pack()

        # Main Content
        main_frame = Frame(self.root)
        main_frame.pack(side="top", fill="both", expand=True)

        # Left Column (Buttons + Scrollable Area)
        left_frame = Frame(main_frame, width=200, bg=background)
        left_frame.pack(side="left", fill="y")

        # Camera Button
        Button(
            left_frame,
            text="Camera",
            command=self.switch_to_camera,
            width=20,
            bg=background_light,
            fg=button_fg,
            font=("Helvetica", 12),
        ).pack(pady=10, padx=10)

        # Scrollable Area for Photos
        self.canvas = Canvas(left_frame, bg=background)
        self.scrollable_frame = Frame(self.canvas, bg=background)
        self.scrollbar = Scrollbar(
            left_frame, orient="vertical", command=self.canvas.yview, bg=background
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        # Right Column (Video Feed)
        video_frame = Frame(main_frame, bg=background)
        video_frame.pack(side="left", fill="both", expand=True)

        self.video_panel = Label(video_frame, bg=background)
        self.video_panel.pack(fill="both", expand=True)

        # Take Picture Button
        Button(
            video_frame,
            text="Take Picture",
            command=self.take_picture,
            width=15,
            bg=button_color,
            fg=button_fg,
            font=("Helvetica", 12),
        ).pack(pady=10)

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def switch_to_camera(self):
        if self.displaying_image:
            self.displaying_image = False
            print("Switched back to camera view.")

    def take_picture(self):
        if self.current_frame is not None:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            if not os.path.exists("photos"):
                os.mkdir("photos")

            filename = f"photos/photo_{timestamp}.jpg"
            cv2.imwrite(filename, self.current_frame)
            print(f"Picture saved as {filename}")

            # Add the photo path to the list
            self.photo_paths.append(filename)

            # Display the thumbnail in the scrollable area
            self.add_thumbnail(filename)

    def add_thumbnail(self, image_path):
        # Resize image to thumbnail size
        img = Image.open(image_path)
        img.thumbnail((150, 150))

        img_tk = ImageTk.PhotoImage(img)

        # Add to frame
        thumbnail_label = Label(
            self.scrollable_frame,
            image=img_tk,
            relief="flat",
        )
        thumbnail_label.image = img_tk  # Keep a reference to avoid garbage collection
        thumbnail_label.pack(pady=5, padx=5)

        # Bind click event to display the full image
        thumbnail_label.bind(
            "<Button-1>", lambda e: self.display_full_image(image_path)
        )

    def display_full_image(self, image_path):
        self.displaying_image = True
        img = Image.open(image_path)
        img = img.resize((self.size[0], self.size[1]), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        self.video_panel.imgtk = img_tk
        self.video_panel.configure(image=img_tk)
        print(f"Displaying full image: {image_path}")

    def quit_app(self):
        self.running = False
        self.cap.release()
        self.root.destroy()
        cv2.destroyAllWindows()

    def process_video(self):
        hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.7)
        prox_threshold = 700

        while self.running:
            if not self.displaying_image:
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Flip the frame horizontally
                frame = cv2.flip(frame, 1)

                # Convert the frame to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Perform hand detection
                results = hands.process(rgb_frame)

                # Perform face detection
                face_results = face_detection.process(rgb_frame)

                face_centroids = []
                hand_centroids = []

                if face_results.detections:
                    self.face_count = len(face_results.detections)
                    self.face_count_var.set(f"Faces Detected: {self.face_count}")

                    for detection in face_results.detections:
                        mp_drawing.draw_detection(frame, detection)
                        bbox = detection.location_data.relative_bounding_box
                        ih, iw, _ = frame.shape
                        x = int(bbox.xmin * iw)
                        y = int(bbox.ymin * ih)
                        w = int(bbox.width * iw)
                        h = int(bbox.height * ih)
                        face_centroids.append(get_centroid((x, y, w, h)))
                else:
                    self.face_count_var.set(f"No Faces Detected")

                #cv2.putText(frame, f"Faces: {self.face_count}", (100, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Draw hand landmarks on the frame
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:

                        # draw hand landmarks
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        # Compute hand centroid
                        x = int(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x * frame.shape[1])
                        y = int(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y * frame.shape[0])
                        hand_centroids.append((x, y))

                        # Determine left or right hand
                        hand_type = "Left" if hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x < 0.5 else "Right"
                        cv2.putText(frame, f"{hand_type} Hand", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                        # Associate hands with faces
                        hand_face_associations = associate_hands(hand_centroids, face_centroids, prox_threshold)

                        # Draw associations - remove when app is almost ready
                        for hand, face in hand_face_associations:
                            cv2.line(frame, hand, face, (50, 255, 0), 2)
                            cv2.putText(
                                frame,
                                "Associated",
                                (hand[0] - 20, hand[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (255, 0, 0),
                                2,
                            )

                        try:
                            # Recognize gestures
                            gesture = recognize_gesture(hand_landmarks)
                            cv2.putText(frame, gesture, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        except AttributeError as e:
                            print("Error recognizing gesture:", e)
                            gesture = "Unknown Gesture"


                else:
                    self.face_count_var.set("No Faces Detected")

                # Store the current frame for capturing
                self.current_frame = frame.copy()

                # Resize and process the frame
                frame = cv2.resize(frame, self.size)
                boxes, weights = self.hog.detectMultiScale(frame, winStride=(8, 8))
                boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])

                for xA, yA, xB, yB in boxes:
                    cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)

                # Convert PIL image to tkinter image
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                imgtk = ImageTk.PhotoImage(image=img)

                # Update video panel
                self.video_panel.imgtk = imgtk
                self.video_panel.configure(image=imgtk)




if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()