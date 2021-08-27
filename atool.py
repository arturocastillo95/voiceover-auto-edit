import pygame
import pyaudio
import wave
import numpy as np
import sys
import os
from shutil import rmtree, copyfile

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

KEEP_THRESHOLD = 0.013 # a chunk will only t labeled as "having content" if the absolute value of the min or max exceeds this threshold.
KEEP_MARGIN = 4 # number of chunks around a "content-filled chunk" to be kept!
EDGE_MARGIN = 3 # this many chunks at the start or end of a chunk will NOT be included (to avoid the sound of the space bar being pressed, etc.)

def createPath(s):
    try:  
        os.mkdir(s)
    except OSError:  
        assert False, "Creation of the directory %s failed. (The TEMP folder may already exist. Delete or rename it, and try again.)"

def deletePath(s):
    try:  
        rmtree(s,ignore_errors=False)
    except OSError:  
        print ("Deletion of the directory %s failed" % s)
        print(OSError)

def get_min_max(arr):
    keep = 0
    minv = np.nanmin(arr)/32768
    maxv = np.nanmax(arr)/32768

    #Check If chunk haves content 
    if abs(minv) >= KEEP_THRESHOLD or abs(maxv) >= KEEP_THRESHOLD:
        keep = 1
    return np.array([[minv, maxv, keep]])

def write_file(frames, session):
    wf = wave.open('test1.wav', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(session.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def trim_audio(frames, keep_data):
    frames_with_content = []

    leng = len(frames)

    for i in range(EDGE_MARGIN, leng-EDGE_MARGIN):
        keep_margin_start = max(0,i-KEEP_MARGIN)
        keep_margin_end = min(leng, i+KEEP_MARGIN+1)

        if np.sum(keep_data[keep_margin_start:keep_margin_end,2]) >= 1:
            frames_with_content.append(frames[i])

    return frames_with_content


def stop_recording(stream, session, frames, keep_data):

    frames = trim_audio(frames, keep_data)

    write_file(frames, session)

    stream.stop_stream()
    stream.close()
    session.terminate()
    sys.exit()

def next_line():
    print('NEXT')

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
    keep_data = np.zeros((0,3))

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()

            if event.type == pygame.KEYDOWN:
                stop_recording(stream, p, frames, keep_data)

        screen.fill(white)
        pygame.display.flip()
        data = stream.read(CHUNK)

        #Decide If audio haves content and if we keep it
        np_data = np.frombuffer(data, dtype=np.int16)
        current_chunk = get_min_max(np_data)

        print(current_chunk)

        keep_data = np.concatenate([keep_data, current_chunk])

        #Display audio visualization

        #Add audio data to file
        frames.append(data)


# print("* done recording")

if __name__=='__main__':
    main()