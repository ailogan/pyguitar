#!/usr/bin/python

# synthomatic.py
#
# Andrew Logan - 1/11/14
#
# Because why not make music the hardest way possible?

import cProfile

import sys

import struct

import data_provider

import pyaudio
import wave

#http://web.mit.edu/music21/
#import music21

import musicxml_parse_test

import argparse

import time

def make_freqs_from_notearray(notearray):
    freqs = []

    for note_data in notearray:
        when = note_data[0]
        note = note_data[1]
        duration_in_ms = note_data[2]

        duration_in_sec = (duration_in_ms / 1000)

        freq = None

        if(note.step is None):
            #This is a rest
            freqs.append([[], duration_in_sec])
            continue

        freq = note.freq

        #Update the previous entry if this note is part of a chord
        if(note.is_chord_member):
            chord_freqs = freqs[-1][0]
            chord_freqs.extend([freq])

        else:
            freqs.append([[freq], duration_in_sec])
        
    return freqs

def main(argv=None):
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--infile", help="path to a musicXML file")

    args = parser.parse_args()

    song = None

    if(args.infile):
        print "Loading..."
        music_xml = musicxml_parse_test.mxl_container(args.infile)
        notearray = music_xml.get_note_array()

    song = make_freqs_from_notearray(notearray)

    #44.1KHz is actually kind of pushing it, so do half that.
    sample_rate = 22050

    print "Opening audio device..."
    #Open the audio interface
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=sample_rate,
                    output=True)
    print "Playing!"

    #And play!
    for notes in song:
        hertzen = notes[0]
        is_rest = False


        if(len(hertzen) == 0):
            is_rest = True

        if (is_rest):
            print "{0:3.2f} R".format(notes[1])
            time.sleep(notes[1])
            continue

        oscillators = []

        hertz_string = ""
        for hertz in hertzen:
            hertz_string += "{0:9.2f} ".format(hertz)

        print "{0:3.2f} {1}".format(notes[1], hertz_string)
        test_osc = data_provider.multi_oscillator(hertzen, sample_rate_in_hz=sample_rate, volume = .1, chunksize=1)

        #Odd that time.clock() seems to run too slowly on a powerbook.  Maybe it's scaled because it's returning processor time?
        starttime = time.time()

        #Hold each note for some amount of time
        while((time.time() - starttime) < notes[1]):
            data = test_osc.get_data()
            data_struct = struct.pack('f'*len(data), *data)
            data_buffer = buffer(data_struct)
            stream.write(data_buffer)

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main())
