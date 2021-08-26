import pygame
import pyaudio
import wave
import numpy as np
import sys

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

KEEP_THRESHOLD = 0.013 # a chunk will only t labeled as "having content" if the absolute value of the min or max exceeds this threshold.
KEEP_MARGIN = 4 # number of chunks around a "content-filled chunk" to be kept!
EDGE_MARGIN = 3 # this many chunks at the start or end of a chunk will NOT be included (to avoid the sound of the space bar being pressed, etc.)

def write_file(frames, audio):
    wf = wave.open('test.wav', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def pause_recording(stream, audio , frames):

    write_file(frames, audio)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    sys.exit()

def next_line():
    print('NEXT!')

def getMinMax(arr):
    keep = 0
    minv = np.nanmin(arr)/32768
    maxv = np.nanmax(arr)/32768

    if abs(minv) >= KEEP_THRESHOLD or abs(maxv) >= KEEP_THRESHOLD:
        keep = 1
    return np.array([[minv, maxv, keep]])

def main():
    size = width, height = 1280, 720
    white = 255, 255, 255

    screen = pygame.display.set_mode(size)

    #Initialize pyaudio and stream
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)
    
    print("* recording")

    frames = []

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()

            if event.type == pygame.KEYDOWN:
                pause_recording(stream, p ,frames)

        screen.fill(white)
        pygame.display.flip()
        data = stream.read(CHUNK)
        print(data)

        #Decide if I audio haves content

        #Display audio visualization

        #Add audio data to file
        frames.append(data)

# print("* done recording")

if __name__=='__main__':
    main()