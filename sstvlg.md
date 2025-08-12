# SSTV Line Generator doc
> thanks mistral for this doc

A Python module for generating SSTV (Slow Scan Television) audio signals from image lines, specifically implementing the Robot8BW mode. This is particularly useful for amateur radio applications where images are transmitted as audio tones.

## Installation

```bash
pip install pillow numpy
```

## Basic Usage

### 1. Initializing the Generator
```python
from sstv_line_generator import SSTVLineGenerator

# Create generator with default settings (48kHz, 16-bit)
generator = SSTVLineGenerator()

# Or with custom settings
generator = SSTVLineGenerator(samples_per_sec=44100, bits=16)
```

### 2. Generating SSTV from Pixel Data
```python
# Create a simple black-to-white gradient line
pixel_line = [i for i in range(256)]  # 256 shades from black to white

# Generate audio samples
samples = generator.generate_samples(pixel_line)

# Save as WAV file
generator.save_line_to_wav(pixel_line, "gradient.wav")
```

### 3. Processing Image Lines
```python
# Generate SSTV from a specific line in an image
generator.save_line_from_image_to_wav("input.jpg", line_number=10, output_filename="line10.wav")

# Get WAV data without saving to disk
wav_data = generator.get_wav_data_from_image("input.jpg", line_number=20)
```

### 4. Convenience Function
```python
from sstv_line_generator import generate_sstv_line

# Quick generation without creating a generator instance
samples = generate_sstv_line([0, 128, 255, 128, 0])  # Black-gray-white-gray-black pattern
```

## Advanced Examples

### 1. Creating a Complete SSTV Transmission
```python
from PIL import Image

# Create a test image (160x100 pixels)
img = Image.new('L', (160, 100))
pixels = img.load()
for y in range(100):
    for x in range(160):
        pixels[x, y] = int((x + y) % 256)  # Simple pattern
img.save("test_pattern.png")

# Process each line and combine into a single WAV
from array import array
import wave

all_samples = array('h')  # 16-bit samples
for line in range(100):
    samples = generator.generate_line_from_image("test_pattern.png", line)
    all_samples.extend(samples)

# Save combined WAV
with wave.open("full_transmission.wav", 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)  # 16-bit
    wav.setframerate(48000)
    wav.writeframes(all_samples)
```

### 2. Custom Pixel Processing
```python
# Create a custom pixel line with text pattern
def create_text_line(text, width=160):
    line = [0] * width
    for i, char in enumerate(text):
        # Simple ASCII art conversion
        code = ord(char)
        for bit in range(8):
            if i*8 + bit < width:
                line[i*8 + bit] = 255 if (code >> bit) & 1 else 0
    return line

text_line = create_text_line("HELLO")
generator.save_line_to_wav(text_line, "text_line.wav")
```

### 3. Real-time Processing
```python
import time

# Simulate real-time transmission (67ms per line)
for line_num in range(100):
    samples = generator.generate_line_from_image("input.jpg", line_num)
    # Here you would send samples to audio output
    # play_audio(samples)  # Implement this based on your audio backend
    time.sleep(0.067)  # Match SSTV timing
```

## Technical Details

### Robot8BW Mode Parameters
| Parameter       | Value  | Description                     |
|-----------------|--------|---------------------------------|
| Image Width     | 160px  | Standard width for Robot8BW     |
| Sync Pulse      | 7ms    | Start of line marker            |
| Pixel Time      | 60ms   | Time for one complete line      |
| Black Frequency | 1500Hz | Frequency for black (0)         |
| White Frequency | 2300Hz | Frequency for white (255)       |
| Sync Frequency  | 1200Hz | Line synchronization frequency  |

### Frequency Mapping
The module converts pixel values (0-255) to frequencies between 1500Hz (black) and 2300Hz (white) using linear interpolation.

### Audio Format
- Default: 48kHz sample rate, 16-bit mono
- Supports 8-bit or 16-bit output
- WAV files are generated in standard PCM format

## API Reference

### SSTVLineGenerator Class

#### `__init__(samples_per_sec=48000, bits=16)`
Initialize the generator with specified audio parameters.

#### `pixel_line_to_frequencies(pixel_line)`
Convert pixel values to frequency/duration tuples.

#### `generate_samples(pixel_line)`
Generate audio samples from pixel values.

#### `save_line_to_wav(pixel_line, filename)`
Save a single line as WAV file.

#### `generate_line_from_image(image_path, line_number)`
Extract and convert a specific line from an image.

#### `save_line_from_image_to_wav(image_path, line_number, output_filename)`
Convenience method to process and save an image line.

### Utility Functions

#### `generate_sstv_line(pixel_line, samples_per_sec=48000, bits=16)`
Quick generation without creating a generator instance.

## Notes

1. The module automatically resizes input lines to 160 pixels (Robot8BW standard)
2. For complete image transmission, you need to process each line sequentially
3. Timing is critical for proper SSTV reception - each line should take exactly 67ms
4. The sync pulse helps receivers identify the start of each line
  
This code is based on [pySSTV](https://github.com/dnet/pySSTV)