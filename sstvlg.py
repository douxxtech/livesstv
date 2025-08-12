#!/usr/bin/env python

# most of this code is based on https://github.com/dnet/pySSTV, check it out !

from __future__ import division
from math import sin, pi
from random import random
from itertools import cycle
from array import array
import wave
from contextlib import closing
from PIL import Image

FREQ_SYNC = 1200
FREQ_BLACK = 1500
FREQ_WHITE = 2300
FREQ_RANGE = FREQ_WHITE - FREQ_BLACK

ROBOT8BW_WIDTH = 160 #px
ROBOT8BW_SYNC = 7  # ms
ROBOT8BW_SCAN = 60  # ms


class SSTVLineGenerator:
    # gens a line of robots8bw sstv from a line of pixels
    # note: a line takes about 67ms to be played

    def __init__(self, samples_per_sec=48000, bits=16):
        self.samples_per_sec = samples_per_sec
        self.bits = bits

    def pixel_line_to_frequencies(self, pixel_line):

        # pixel_line: array of pixel values (grayscale 0-255) or PIL Image row. Will be resized to 160 pixels for Robot8BW
        #
        # returns a list of (frequency, duration_ms) tuples

        # if PIL Image, coverts to bw and gets pixels values
        if hasattr(pixel_line, 'convert'):
            pixel_line = list(pixel_line.convert('L').getdata())


        pixel_line = self._resize_pixel_line(pixel_line, ROBOT8BW_WIDTH)

        freq_tuples = []

        # adds the sync at the end (basically to tell the decoder that the line is done)
        freq_tuples.append((FREQ_SYNC, ROBOT8BW_SYNC))

        # img -> freq
        msec_pixel = ROBOT8BW_SCAN / ROBOT8BW_WIDTH
        for pixel_value in pixel_line:
            pixel_value = max(0, min(255, int(pixel_value)))
            freq = self._byte_to_freq(pixel_value)
            freq_tuples.append((freq, msec_pixel))

        return freq_tuples

    def _resize_pixel_line(self, pixel_line, target_width):

        if len(pixel_line) == target_width:
            return pixel_line

        if len(pixel_line) == 0:
            return [0] * target_width

        resized = []
        scale = (len(pixel_line) - 1) / (target_width - 1) if target_width > 1 else 0

        for i in range(target_width):
            if target_width == 1:
                resized.append(pixel_line[0] if pixel_line else 0)

            else:
                pos = i * scale
                left_idx = int(pos)
                right_idx = min(left_idx + 1, len(pixel_line) - 1)

                if left_idx == right_idx:
                    resized.append(pixel_line[left_idx])
                else:
                    # some wizardry that i found online
                    weight = pos - left_idx
                    value = pixel_line[left_idx] * (1 - weight) + pixel_line[right_idx] * weight
                    resized.append(int(value))

        return resized

    def _byte_to_freq(self, value):
        return FREQ_BLACK + FREQ_RANGE * value / 255

    def generate_samples(self, pixel_line):

        # pixel_line: line of pixels to convert
        #
        # returns an array of audio samples

        freq_tuples = self.pixel_line_to_frequencies(pixel_line)

        fmt = {8: 'b', 16: 'h'}[self.bits]
        samples = array(fmt, self._gen_samples_from_freq_tuples(freq_tuples))
        return samples

    def _gen_samples_from_freq_tuples(self, freq_tuples):

        # according to pyystv we are "performs quantization according to the bits per sample value given during construction"

        max_value = 2 ** self.bits
        alias = 1 / max_value
        amp = max_value // 2
        lowest = -amp
        highest = amp - 1
        alias_cycle = cycle((alias * (random() - 0.5) for _ in range(1024)))

        spms = self.samples_per_sec / 1000
        offset = 0
        samples = 0
        factor = 2 * pi / self.samples_per_sec
        sample = 0

        for freq, msec in freq_tuples:
            samples += spms * msec
            tx = int(samples)
            freq_factor = freq * factor

            for sample in range(tx):
                value = sin(sample * freq_factor + offset)
                # Quantize sample
                quantized = int(value * amp + next(alias_cycle))
                quantized = (lowest if quantized <= lowest else
                           quantized if quantized <= highest else highest)
                yield quantized

            offset += (sample + 1) * freq_factor
            samples -= tx

    def generate_line_from_image(self, image_path, line_number):
        # Generate SSTV audio from a specific line of an image file, can be useful if we dont want to do preprocessing
        #
        # image_path: path to image file (png, jpg, etc.)
        # line_number: which line to extract (0-based)
        #
        # returns an array of audio samples

        pixel_line = self.extract_line_from_image(image_path, line_number)
        return self.generate_samples(pixel_line)

    def get_wav_data_from_image(self, image_path, line_number):

        # image_path: path to image file
        # line_number: which line to extract (0-based)
        #
        # returns cmoplete wav file data in bytes

        pixel_line = self.extract_line_from_image(image_path, line_number)
        return self.get_wav_data(pixel_line)

    def extract_line_from_image(self, image_path, line_number):

        # image_path: path to image file
        # line_number: which line to extract (0-based)
        #
        # returns a list of grayscale pixel values (0-255)

        try:
            image = Image.open(image_path).convert('L')
            width, height = image.size

            # validate line number
            if line_number < 0 or line_number >= height:
                raise ValueError(f"Line number {line_number} out of range. Image height is {height} (valid range: 0-{height-1})")

            pixel_line = []
            for x in range(width):
                pixel_value = image.getpixel((x, line_number))
                pixel_line.append(pixel_value)

            return pixel_line

        except IOError as e:
            raise IOError(f"Could not open image file '{image_path}': {e}")
        except Exception as e:
            raise Exception(f"Error processing image: {e}")

    def save_line_from_image_to_wav(self, image_path, line_number, output_filename):
        # Extract a line from an image and save as wav file
        #
        # image_path: path to image file
        # line_number: which line to extract (0-based)
        # output_filename: output wav filename

        wav_data = self.get_wav_data_from_image(image_path, line_number)
        with open(output_filename, 'wb') as f:
            f.write(wav_data)


    def get_wav_data(self, pixel_line):
        # Get wav file data as bytes without saving to disk
        #
        # pixel_line: line of pixels to convert
        #
        #
        # returns the complete wav file data that can be written to file or used directly, in bytes

        from io import BytesIO

        samples = self.generate_samples(pixel_line)

        wav_buffer = BytesIO()
        with closing(wave.open(wav_buffer, 'wb')) as wav:
            wav.setnchannels(1)  # mono
            wav.setsampwidth(self.bits // 8)
            wav.setframerate(self.samples_per_sec)
            wav.writeframes(samples)

        wav_buffer.seek(0)
        return wav_buffer.read()

    def save_line_to_wav(self, pixel_line, filename):

        # pixel_line: line of pixels to convert
        # filename: output wav filename

        wav_data = self.get_wav_data(pixel_line)
        with open(filename, 'wb') as f:
            f.write(wav_data)


# convenience func
def generate_sstv_line(pixel_line, samples_per_sec=48000, bits=16):

    # pixel_line: list of grayscale values (0-255) or any iterable
    # samples_per_sec: audio sample rate (default: 48000)
    # bits: bits per sample (8 or 16, default: 16)
    #
    # retuns an array of audio samples

    generator = SSTVLineGenerator(samples_per_sec, bits)
    return generator.generate_samples(pixel_line)


if __name__ == "__main__":
    print("Use that as a module")