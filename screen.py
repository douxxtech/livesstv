import sstvlg
import cv2
import pyaudio
import threading
import time
import numpy as np
import os
from PIL import ImageGrab

target_width = 160
pixel_lines = []
pixel_lines_lock = threading.Lock()
line_count = 0
fps = 30

def capture_full_screen():
    try:
        img = ImageGrab.grab()
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Screen capture failed: {e}")
        return None

def screen_capture():
    global pixel_lines, line_count

    while True:
        frame = capture_full_screen()
        
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            print("Capture failed, using black frame")
        
        height, width = frame.shape[:2]
        if width > 0 and height > 0:
            new_height = int(height * (target_width / width))
            resized_frame = cv2.resize(frame, (target_width, new_height)) #doing preprocessing for convenience
            gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

            with pixel_lines_lock:
                pixel_lines = [gray_frame[i, :].copy() for i in range(new_height)]
                line_count = new_height

        time.sleep(1 / fps)

def audio_streaming():
    global pixel_lines, line_count
    generator = sstvlg.SSTVLineGenerator()
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000, output=True)

    line_idx = 0
    while True:
        with pixel_lines_lock:
            if line_idx < len(pixel_lines) and pixel_lines:
                pixel_line = pixel_lines[line_idx]
            else:
                pixel_line = np.zeros(target_width, dtype=np.uint8)

        samples = generator.generate_samples(pixel_line)
        stream.write(samples.tobytes())

        line_idx += 1
        if line_count > 0 and line_idx >= line_count:
            line_idx = 0

def screen_main():
    print("Starting SSTV screen streaming. Code avalible at git.douxx.tech/livesstv")

    global pixel_lines, line_count
    pixel_lines = []
    line_count = 0

    cap_thread = threading.Thread(target=screen_capture, daemon=True)
    cap_thread.start()

    try:
        audio_streaming() #blk
    except KeyboardInterrupt:
        os._exit(0)

if __name__ == "__main__":
    screen_main()