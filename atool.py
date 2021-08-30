import pygame
import pyaudio
import wave
import numpy as np
import sys
import os
from shutil import rmtree, copyfile
import subprocess

pygame.init()
pygame.font.init()

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

KEEP_THRESHOLD = 0.013 # a chunk will only t labeled as "having content" if the absolute value of the min or max exceeds this threshold.
KEEP_MARGIN = 4 # number of chunks around a "content-filled chunk" to be kept!
EDGE_MARGIN = 3 # this many chunks at the start or end of a chunk will NOT be included (to avoid the sound of the space bar being pressed, etc.)

#Pygame variables
size = width, height = 1280, 720
white = 255, 255, 255

def render_text_cenered_at(text, font, colour, x, y, screen, allowed_width):
    # first, split the text into words
    words = text.split()

    # now, construct lines out of these words
    lines = []
    while len(words) > 0:
        # get as many words as will fit within allowed_width
        line_words = []
        while len(words) > 0:
            line_words.append(words.pop(0))
            fw, fh = font.size(' '.join(line_words + words[:1]))
            if fw > allowed_width:
                break

        # add a line consisting of those words
        line = ' '.join(line_words)
        lines.append(line)

    # now we've split our text into lines that fit into the width, actually
    # render them

    # we'll render each line below the last, so we need to keep track of
    # the culmative height of the lines we've rendered so far
    y_offset = 0
    for line in lines:
        fw, fh = font.size(line)

        # (tx, ty) is the top-left of the font surface
        tx = x - fw / 2
        ty = y + y_offset

        font_surface = font.render(line, True, colour)
        screen.blit(font_surface, (tx, ty))

        y_offset += fh

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

def write_file(output_file, frames, session):
    wf = wave.open(output_file, 'wb')
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

def stitch_files(save_file, last_visited_line):
    f = open('TEMP/file_list.txt', 'w+')
    for i in range(0, last_visited_line+1):
        f.write('file ' + str(i) + '.wav\n')
    f.flush()
    f.close()
    command = 'ffmpeg -f concat -safe 0 -i TEMP/file_list.txt -c copy ' + save_file
    subprocess.call(command, shell=True)

    deletePath('TEMP')
        

def stop_recording(save_file, last_visited_line, stream, session):
    global frames
    global keep_data
    global pointer

    frames = trim_audio(frames, keep_data)
    output_file = 'TEMP/' + str(pointer) + '.wav'
    write_file(output_file, frames, session)

    stitch_files(save_file, last_visited_line)

    stream.stop_stream()
    stream.close()
    session.terminate()
    sys.exit()

def start_recording():
    global pointer
    global stream
    global p
    global frames
    global keep_data

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

def reset_recording():
    global frames
    global keep_data

    frames = []
    keep_data = np.zeros((0,3))
    print('Reset current line')

def next_line(session):
    global frames
    global keep_data
    global pointer

    frames = trim_audio(frames, keep_data)
    output_file = 'TEMP/' + str(pointer) + '.wav'
    write_file(output_file, frames, session)

    pointer += 1
    frames = []
    keep_data = np.zeros((0,3))


def main():
    global pointer
    global stream
    global p
    global frames
    global keep_data

    FONT = pygame.font.SysFont('Helvetica', 35)

    screen = pygame.display.set_mode(size)

    file = sys.argv[1]
    SAVE_FILE = sys.argv[2]
    txt = open(file, 'r')
    txt = txt.read()
    lines = txt.split('.')

    pointer = 0

    createPath('TEMP')

    start_recording()

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    stop_recording(SAVE_FILE, pointer, stream, p)
                if event.key == pygame.K_LEFT:
                    reset_recording()
                if event.key == pygame.K_RIGHT:
                    next_line(p)

        screen.fill(white)

        render_text_cenered_at(lines[pointer], FONT, (0,0,0), 640, 360-35, screen, 1200)

        pygame.display.flip()

        data = stream.read(CHUNK)

        #Decide If audio haves content and if we keep it
        np_data = np.frombuffer(data, dtype=np.int16)
        current_chunk = get_min_max(np_data)

        keep_data = np.concatenate([keep_data, current_chunk])

        #Display audio visualization

        #Add audio data to file
        frames.append(data)


# print("* done recording")

if __name__=='__main__':
    main()