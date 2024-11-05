import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import cv2
import mediapipe as mp
import pyautogui

# Global variables for settings
sensitivity = 1.5
is_running = False
scrolling = False
holding_click = False

# Initialize MediaPipe Face Mesh
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
screen_w, screen_h = pyautogui.size()

def set_sensitivity(val):
    global sensitivity
    sensitivity = float(val)
    print(f'Sensitivity set to: {sensitivity}')  # Debugging

def start_stop():
    global is_running
    if not is_running:
        show_tutorial()
    is_running = not is_running
    start_btn.config(text='Stop' if is_running else 'Start')
    print(f'Running state set to: {is_running}')  # Debugging
    if is_running:
        t = threading.Thread(target=track_eye_movement)
        t.daemon = True
        t.start()

def show_tutorial():
    tutorial_message = (
        "Welcome to the Eye Controlled Mouse Tutorial!\n\n"
        "Here are the basic controls:\n"
        "1. Move your eyes to control the cursor.\n"
        "2. Blink your left eye to perform a single click.\n"
        "3. Blink your right eye to perform a double click.\n"
        "4. Look up or down to scroll the screen.\n"
        "5. Long blink with your left eye to hold the mouse button down.\n"
        "Blink again to release the hold.\n\n"
        "Enjoy!"
    )
    tutorial_label.config(text=tutorial_message)
    tutorial_label.pack(pady=10)

def update_frame():
    if is_running:
        _, frame = cam.read()
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.config(image=imgtk)
    root.after(10, update_frame)

def track_eye_movement():
    global is_running, cam, face_mesh, screen_w, screen_h, sensitivity, scrolling, holding_click
    safe_margin = 20

    while is_running:
        _, frame = cam.read()
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = face_mesh.process(rgb_frame)
        landmark_points = output.multi_face_landmarks
        frame_h, frame_w, _ = frame.shape

        if landmark_points:
            print("Landmarks detected")  # Debugging
            landmarks = landmark_points[0].landmark
            pupil = landmarks[468]
            x = int(pupil.x * frame_w)
            y = int(pupil.y * frame_h)
            screen_x = screen_w / frame_w * x * sensitivity
            screen_y = screen_h / frame_h * y * sensitivity

            print(f"Pupil Coordinates: x={x}, y={y}")  # Debugging
            print(f"Screen Coordinates: x={screen_x}, y={screen_y}")  # Debugging

            if safe_margin < screen_x < screen_w - safe_margin and safe_margin < screen_y < screen_h - safe_margin:
                pyautogui.moveTo(screen_x, screen_y, duration=0.1)  # Smooth movement

            left_eye = [landmarks[145], landmarks[159]]
            right_eye = [landmarks[374], landmarks[386]]

            # Scroll detection
            if y < frame_h // 4:
                if not scrolling:
                    print("Scrolling up")  # Debugging
                    pyautogui.scroll(1)
                    scrolling = True
            elif y > frame_h * 3 // 4:
                if not scrolling:
                    print("Scrolling down")  # Debugging
                    pyautogui.scroll(-1)
                    scrolling = True
            else:
                scrolling = False

            # Blink detection for clicking
            for landmark in left_eye:
                x = int(landmark.x * frame_w)
                y = int(landmark.y * frame_h)
                cv2.circle(frame, (x, y), 3, (255, 0, 255), -1)
            if abs(left_eye[0].y - left_eye[1].y) < 0.004:
                print("Left eye blink detected")  # Debugging
                pyautogui.click()
                pyautogui.sleep(0.5)

            for landmark in right_eye:
                x = int(landmark.x * frame_w)
                y = int(landmark.y * frame_h)
                cv2.circle(frame, (x, y), 3, (255, 0, 255), -1)
            if abs(right_eye[0].y - right_eye[1].y) < 0.004:
                print("Right eye blink detected")  # Debugging
                pyautogui.doubleClick()
                pyautogui.sleep(0.5)

            # Hold clicking detection
            if abs(left_eye[0].y - left_eye[1].y) < 0.002 and not holding_click:
                print("Hold click start")  # Debugging
                pyautogui.mouseDown()
                holding_click = True
            elif abs(left_eye[0].y - left_eye[1].y) > 0.004 and holding_click:
                print("Hold click end")  # Debugging
                pyautogui.mouseUp()
                holding_click = False

    cam.release()

# Create GUI
root = tk.Tk()
root.title("Eye Controlled Mouse")

sensitivity_label = tk.Label(root, text="Sensitivity")
sensitivity_label.pack()
sensitivity_slider = tk.Scale(root, from_=0.1, to=5.0, orient=tk.HORIZONTAL, resolution=0.1, command=set_sensitivity)
sensitivity_slider.set(sensitivity)
sensitivity_slider.pack()

start_btn = tk.Button(root, text="Start", command=start_stop)
start_btn.pack()

tutorial_label = tk.Label(root, text="")
tutorial_label.pack()

video_label = tk.Label(root)
video_label.pack()

root.after(10, update_frame)
root.mainloop()
