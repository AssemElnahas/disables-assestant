import tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
import speech_recognition as sr
import pyaudio
import time
import pyttsx3
import matplotlib.pyplot as plt
from tkinter import messagebox

# Initialize the pyttsx3 engine for text-to-speech
engine = pyttsx3.init()

# Function to generate and play a tone for hearing testing
def generate_tone(frequency, duration, volume=1.0):
    p = pyaudio.PyAudio()
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    wave = np.sin(2 * np.pi * frequency * t) * volume
    wave = (wave * 32767).astype(np.int16)

    stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True)
    stream.write(wave.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()

# Function to start the hearing test
def start_voice_testing():
    frequencies = [250, 500, 1000, 2000, 4000, 8000]
    duration = 1.0
    volume = 0.5
    results = []
    
    for freq in frequencies:
        generate_tone(freq, duration, volume)
        time.sleep(1.5)
        heard = messagebox.askyesno("Did you hear the sound?", f"Did you hear the tone at {freq} Hz?")
        results.append(heard)
        if heard:
            messagebox.showinfo("Info", f"You heard the frequency {freq} Hz.")
        else:
            messagebox.showinfo("Info", f"You did not hear the frequency {freq} Hz.")
    
    plot_results(frequencies, results)

# Function to plot the results
def plot_results(frequencies, results):
    result_values = [1 if r else 0 for r in results]
    plt.figure(figsize=(8, 6))
    plt.plot(frequencies, result_values, marker='o', linestyle='-', color='b', label='Hearing response')
    plt.title("Hearing Test Results")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Response (1 = audible, 0 = inaudible)")
    plt.xticks(frequencies)
    plt.yticks([0, 1], ["inaudible", "audible"])
    plt.grid(True)
    plt.legend()
    plt.show()

# Global variables for video capture and brightness/contrast
cap = None
brightness = 1.0
contrast = 1.0

def calculate_distance_from_size(edges):
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        focal_length = 800
        real_width = 100
        if w > 0:
            distance = (real_width * focal_length) / w
            return distance, (x, y, w, h)
    return None, None

# Function to start wall detection
def start_wall_detection():
    global cap, panel, brightness, contrast
    cap = cv2.VideoCapture(0)
    
    def update_frame():
        ret, frame = cap.read()
        if ret:
            frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness * 50)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            distance, bounding_box = calculate_distance_from_size(edges)
            
            if distance is not None and distance < 500:
                wall_label.config(text=f"Wall detected! Approx. distance: {distance:.2f} cm")
                engine.say(f"Warning! Wall detected at {distance:.2f} centimeters.")
                engine.runAndWait()
                x, y, w, h = bounding_box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                wall_label.config(text="No walls detected.")
            
            frame = cv2.resize(frame, (320, 240))
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            panel.imgtk = imgtk
            panel.config(image=imgtk)
        
        panel.after(10, update_frame)
    
    update_frame()

# Function to stop wall detection
def stop_wall_detection():
    global cap
    if cap:
        cap.release()
    panel.config(image=None)
    wall_label.config(text="")

# Function to start English speech recognition
def start_speech_recognition_English():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text="Adjusting for ambient noise...")
        root.update()
        recognizer.adjust_for_ambient_noise(source)
        status_label.config(text="Start speaking...")
        audio = recognizer.listen(source)
        
        try:
            status_label.config(text="Recognizing your speech...")
            text = recognizer.recognize_google(audio, language="en-US")
            result_label.config(text=f"You said: {text}")
        except sr.UnknownValueError:
            result_label.config(text="I didn't understand what you said.")
        except sr.RequestError:
            result_label.config(text="Error with Google service; check your connection.")

# Function to adjust brightness
def adjust_brightness(val):
    global brightness
    brightness = float(val)

# Function to adjust contrast
def adjust_contrast(val):
    global contrast
    contrast = float(val)

# Braille recognition
def recognize_braille():
    braille_dict = {
        (1,): 'A', (1, 2): 'B', (1, 4): 'C', (1, 4, 5): 'D', (1, 5): 'E',
        (1, 2, 4): 'F', (1, 2, 4, 5): 'G', (1, 2, 5): 'H', (2, 4): 'I', (2, 4, 5): 'J',
        (1, 3): 'K', (1, 2, 3): 'L', (1, 3, 4): 'M', (1, 3, 4, 5): 'N', (1, 3, 5): 'O',
        (1, 2, 3, 4): 'P', (1, 2, 3, 4, 5): 'Q', (1, 2, 3, 5): 'R', (2, 3, 4): 'S', (2, 3, 4, 5): 'T',
        (1, 3, 6): 'U', (1, 2, 3, 6): 'V', (2, 4, 5, 6): 'W', (1, 3, 4, 6): 'X', (1, 3, 4, 5, 6): 'Y', (1, 3, 5, 6): 'Z'
    }
    
    selected_dots = []
    
    if braille_cells[0].get(): selected_dots.append(1)
    if braille_cells[1].get(): selected_dots.append(2)
    if braille_cells[2].get(): selected_dots.append(3)
    if braille_cells[3].get(): selected_dots.append(4)
    if braille_cells[4].get(): selected_dots.append(5)
    if braille_cells[5].get(): selected_dots.append(6)
    
    selected_tuple = tuple(sorted(selected_dots))
    letter = braille_dict.get(selected_tuple, "Unknown")
    
    braille_result_label.config(text=f"Braille Input: {letter}")
    
    try:
        engine.say(f"You selected the letter {letter}")
        engine.runAndWait()
    except Exception as e:
        print(f"Error with pyttsx3: {e}")

# Main Tkinter window
root = tk.Tk()
root.title("Wall Detection, Speech-to-Text, and Braille Recognition")
root.geometry('600x850')
root.configure(bg="#601cfc")

# Notebook or Frame for the UI categories
notebook = tk.Frame(root, bg='#3a6cf4')
notebook.pack(pady=10, padx=10)

# Speech-to-Text Category
category_label = tk.Label(notebook, text="Speech Recognition in English", font=("Arial", 16))
category_label.grid(row=0, column=0, padx=10, pady=5)

status_label = tk.Label(notebook, text="Press the button and start talking", font=("Arial", 12))
status_label.grid(row=1, column=0, padx=10, pady=5)

recognize_button = tk.Button(notebook, text="Start Speech Recognition", font=("Arial", 14), command=start_speech_recognition_English)
recognize_button.grid(row=2, column=0, padx=10, pady=5)

result_label = tk.Label(notebook, text="", font=("Arial", 12), wraplength=400)
result_label.grid(row=3, column=0, padx=10, pady=5)

# Wall Detection Category
wall_detection_label = tk.Label(notebook, text="Wall Detection", font=("Arial", 16))
wall_detection_label.grid(row=4, column=0, padx=10, pady=5)

panel = tk.Label(notebook)
panel.grid(row=5, column=0, padx=10, pady=5)

wall_label = tk.Label(notebook, text="No walls detected", font=("Arial", 12))
wall_label.grid(row=6, column=0, padx=10, pady=5)

start_wall_button = tk.Button(notebook, text="Start Wall Detection", font=("Arial", 14), command=start_wall_detection)
start_wall_button.grid(row=7, column=0, padx=10, pady=5)

stop_wall_button = tk.Button(notebook, text="Stop Wall Detection", font=("Arial", 14), command=stop_wall_detection)
stop_wall_button.grid(row=8, column=0, padx=10, pady=5)

# Braille Reading Category
braille_label = tk.Label(notebook, text="Braille Recognition", font=("Arial", 16))
braille_label.grid(row=9, column=0, padx=10, pady=5)

braille_cells = [tk.IntVar() for _ in range(6)]
for i in range(6):
    tk.Checkbutton(notebook, text=f"Dot {i+1}", variable=braille_cells[i], font=("Arial", 12)).grid(row=10+i, column=0, padx=10, pady=2)

braille_result_label = tk.Label(notebook, text="Braille Input: ", font=("Arial", 14))
braille_result_label.grid(row=16, column=0, padx=10, pady=5)

braille_button = tk.Button(notebook, text="Recognize Braille", font=("Arial", 14), command=recognize_braille)
braille_button.grid(row=17, column=0, padx=10, pady=5)

root.mainloop()
