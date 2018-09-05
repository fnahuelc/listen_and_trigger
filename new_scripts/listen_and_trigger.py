from __future__ import division
import os
import time
import wave
import struct
import billiard as multiprocessing
import pyaudio

FORMAT = pyaudio.paInt16
FORMAT_UNPACK = "%dh"
FORMAT_MAX_VALUE = 32767

CHANNELS = 1
RATE = 44100
INPUT_FRAMES_PER_BLOCK = 128
INPUT_BLOCK_TIME = INPUT_FRAMES_PER_BLOCK / RATE

Treshold_db = -6
THRESHOLD = 10 ** (Treshold_db/10)

MAX_TIME_WAITING = 10
MIN_TIME_WAITING = 1


class ListenAndTrigger:
    def __init__(self):
        self.pa = pyaudio.PyAudio()

    def _set_capture(self):
        self.capture = self.pa.open(
            format=FORMAT,  # |
            channels=CHANNELS,  # |---- You always use this in pyaudio...
            rate=RATE,  # |
            input=True,  # |
            frames_per_buffer=INPUT_FRAMES_PER_BLOCK
        )
        self.width = self.pa.get_sample_size(FORMAT)

    def _set_reproduction(self):
        self.wf = wave.open("../wav_files/ECC_test_FE_signal_3.95V.wav", 'rb')
        self.reproduction = self.pa.open(
            format=self.pa.get_format_from_width(self.wf.getsampwidth()),
            channels=self.wf.getnchannels(),
            rate=self.wf.getframerate(),
            output=True
        )

    def _check_trigger(self):
        print("Listening...")
        total_time = 0
        self.how_many = 0
        while total_time <= MAX_TIME_WAITING:
            if self.__pulse() and total_time > MIN_TIME_WAITING:
                return True
            total_time += INPUT_BLOCK_TIME
            self.how_many += 1
            time.sleep(INPUT_BLOCK_TIME)
        return False

    def __pulse(self):
        block = self.capture.read(INPUT_FRAMES_PER_BLOCK)
        count = len(block) / self.width
        shorts = struct.unpack(FORMAT_UNPACK % count, block)
        amplitude = max(shorts)/FORMAT_MAX_VALUE
        return amplitude > THRESHOLD

    def _play_sound(self):
        print "Playing..."
        data = self.wf.readframes(INPUT_FRAMES_PER_BLOCK)
        while data != '':
            self.reproduction.write(data)
            data = self.wf.readframes(INPUT_FRAMES_PER_BLOCK)

    def _close_audio_ports(self):
        self.capture.stop_stream()
        self.capture.close()
        self.reproduction.stop_stream()
        self.reproduction.close()
        self.pa.terminate()

    def init(self):
        self._set_capture()
        self._set_reproduction()
        if self._check_trigger():
            self._play_sound()
        self._close_audio_ports()


if __name__ == "__main__":
    ListenAndTrigger().init()
