import sstvlg
import cv2
import pyaudio
import threading
import time
import os

target_width = 160
pixel_lines = []
pixel_lines_lock = threading.Lock()
line_count = 0
fps = 30

def webcam_capture():
    global pixel_lines, line_count
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        height, width, _ = frame.shape
        aspect_ratio = height / width
        line_count = int(target_width * aspect_ratio)
        
        resized_frame = cv2.resize(frame, (target_width, line_count)) #doing preprocessing for convenience
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
        
        with pixel_lines_lock:
            pixel_lines = [gray_frame[i, :].copy() for i in range(line_count)]
        
        time.sleep(1 / fps)

    cap.release()

def audio_streaming():
    global pixel_lines, line_count
    
    generator = sstvlg.SSTVLineGenerator()
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000, output=True)
    
    line_idx = 0
    while True:
        with pixel_lines_lock:
            if line_idx < len(pixel_lines):
                pixel_line = pixel_lines[line_idx]
            else:
                # fallback to a blank line if no pixels
                pixel_line = [0] * target_width
        
        samples = generator.generate_samples(pixel_line)
        stream.write(samples.tobytes())
        
        line_idx += 1
        if line_idx >= line_count:
            line_idx = 0

def cam_main():
    print("Starting SSTV webcam streaming. Code avalible at git.douxx.tech/livesstv")

    global pixel_lines, line_count
    pixel_lines = [[0]*target_width] * target_width
    
    cap_thread = threading.Thread(target=webcam_capture, daemon=True)
    cap_thread.start()
    
    try:
        audio_streaming() #blk
    except KeyboardInterrupt:
        os._exit(0)

if __name__ == "__main__":
    cam_main()
