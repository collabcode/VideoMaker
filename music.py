#!/usr/bin/python
# coding=utf-8

import numpy
import random
import math
import copy
import pyaudio
from tkinter import *


class NoteGen(object):
    def __init__(self, notes=range(30, 70)):
        self.choices = list(map(self._note, notes))
        self.possibilities = copy.copy(self.choices)
        self.mapping = {}

    def __call__(self, key, duration=float("inf"), amplitude=1):
        note = self._get(key, duration, amplitude)
        if not note:
            note = self._map(key, duration, amplitude)
        return note

    def _map(self, key, duration, amplitude):
        if not self.possibilities:
            self.mapping[key] = random.choice(self.choices)
            return Note(self.mapping[key], duration, amplitude)

        n = self.possibilities[0]
        # n = random.choice(self.possibilities)
        self.possibilities.remove(n)
        self.mapping[key] = n
        return Note(n, duration, amplitude)

    def _get(self, key, duration, amplitude):
        if key in self.mapping:
            return Note(self.mapping[key], duration, amplitude)

    def _note(self, n):
        return math.pow(2, (float(n) - 49) / 12) * 440


class Note(object):
    names = [
        "A",
        "A#/Bf",
        "B",
        "C",
        "C#/Df",
        "D",
        "D#/Ef",
        "E",
        "F",
        "F#/Gf",
        "G",
        "G#/Af"
    ]

    def __init__(self, frequency=440, duration=float("inf"), amplitude=1, rate=44100):
        self.frequency = frequency
        self.total_frames = duration * rate
        self.frame_offset = 0
        self.rate = rate
        self.amplitude = amplitude

    def __call__(self, frames):
        if self.done:
            return numpy.zeros(frames, float)

        factor = float(self.frequency) * ((math.pi * 2) / self.rate)

        length = (frames if frames < self.remaining else self.remaining)
        sin = numpy.sin((numpy.arange(length) + self.frame_offset) * factor) * self.amplitude
        if frames > self.remaining:
            sin = numpy.concatenate([sin, numpy.zeros(frames - self.remaining, float)])

        self.frame_offset += frames
        return sin

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __eq__(self, other):
        return self.frequency == other.frequency

    @property
    def remaining(self):
        return self.total_frames - self.frame_offset

    @property
    def done(self):
        return self.frame_offset >= self.total_frames

    @property
    def name(self):
        keynum = int((12 * math.log((self.frequency / 440), 2)) + 48) % 12
        return self.names[keynum]


class Chord(object):
    def __init__(self):
        self.notes = []

    def __call__(self, duration):
        if not len(self.notes):
            return numpy.zeros(duration, float)

        gen = lambda note: note(duration)
        output = sum(map(gen, self.notes))
        self.clean()
        return output

    def add_note(self, note):
        if not isinstance(note, Note):
            raise ValueError("Must be of type Note")

        self.notes.append(note)

    def remove_note(self, note):
        if not isinstance(note, Note):
            return

        if note in self.notes:
            self.notes.remove(note)

    def clean(self):
        for note in self.notes:
            if note.done:
                self.notes.remove(note)


if __name__ == "__main__":
    p = pyaudio.PyAudio()
    chord = Chord()
    gen = NoteGen()


    def callback(in_data, frame_count, time_info, status):
        wave = chord(frame_count)
        data = wave.astype(numpy.float32).tostring()
        return (data, pyaudio.paContinue)


    stream = p.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=44100,
        output=True,
        stream_callback=callback
    )

    stream.start_stream()


    def keydown(event):
        k = gen(event.char, 1)
        chord.add_note(k)
        for n in chord.notes:
            print[(n.name, n.frequency)]


    def keyup(event):
        pass
        # k = gen(event.char)
        # chord.remove_note(k)
        # print [n.name for n in chord.notes]


    root = Tk()
    frame = Frame(root, width=100, height=100)
    frame.bind_all("<KeyPress>", keydown)
    frame.bind_all("<KeyRelease>", keyup)
    frame.pack()

    root.mainloop()

    stream.stop_stream()
    stream.close()
    p.terminate()