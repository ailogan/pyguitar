#!/usr/bin/python

# synthomatic.py
#
# Andrew Logan - 1/11/14
#
# Because why not make music the hardest way possible?

import sys

import struct

import data_provider

import pyaudio
import wave

#http://web.mit.edu/music21/
#import music21

import musicxml_parse_test

import numpy as np

import argparse

import time

def key_to_freq(key):
    # Derived from https://en.wikipedia.org/wiki/Piano_key_frequencies
    #
    # Key 1 is A0, key 88 is C8
    print key

    num_harmonics = 5

    twelfth_root_of_two = np.power(2, float(1)/12)
    freq = (np.power(twelfth_root_of_two, (key - 49)) * 440)

    freq_array = []

    #Fundamental tone
    #freq_array.append(freq)

    #Odd harmonics are woodwind-esque.
    #for x in range(1, (num_harmonics * 2) + 1, 2):
    #    freq_array.append(freq * x)

    #Even harmonics
    #for x in range(2, (num_harmonics * 2) +1, 2):
    #    freq_array.append(freq * x)


    #And all of the harmonics are more like an organ
    for x in range(1, (num_harmonics + 1)):
        freq_array.append(freq * x)

    return freq_array

def make_notes_from_notearray(notearray):
    notes = []
    for note_data in notearray:
        when = note_data[0]
        note = note_data[1]
        duration_in_ms = note_data[2]

        #My cheesy format can't handle chords yet.
        if(note.is_chord_member):
            continue

        key = ""
        
        #format is: (piano_key_#, duration (seconds-ish)) ("R" is a rest)
        
        if(note.step is None):
            key = "R"

        else:
            key = note_to_key(note)
            print key
            
        duration_in_sec = (duration_in_ms / 1000)
        
        notes.append((key, duration_in_sec))

    return notes

def note_to_key(note):
    step = note.step
    alter = note.alter  #sharps are positive
    octave = note.octave

    #A0 is 1, C1 is 4

    #A is the first note in a 12-tone scale, D is the 6th, etc.
    step_to_num = {'A' : 1,
                   'B' : 3,
                   'C' : 4,
                   'D' : 6,
                   'E' : 8,
                   'F' : 9,
                   'G' : 11}


    #And handle sharps or flats
    step_num = step_to_num[step]

    if(alter is not None):
        step_num + alter

    #Octaves start at C
    if(step_num > 3):
        octave -= 1

    #And calculate the key number.
    key_num = step_num  + (octave * 12)

    print "{0}{1} is {2}".format(note.step, note.octave, key_num)

    return key_num

def get_default_notes():
    #First couple notes of Also Sprach Zarathustra.
    #format is: (piano_key_#, duration (seconds-ish))
    #notes = [(40,1),(47,1),(52,1),(44,.25),(43,2)]
    
    #the star wars theme is a fine default.
    notes = [ (38,1), (45,1), (43,.25), (42,.25), (40,.25), (50,1),
              (45,1), (43,.25), (42,.25), (40,.25), (50,1),
              (45,1), (43,.25), (42,.25), (43,.25), (40,1),
             
             #repeat
              (38,1), (45,1), (43,.25), (42,.25), (40,.25), (50,1),
              (45,1), (43,.25), (42,.25), (40,.25), (50,1),
              (45,1), (43,.25), (42,.25), (43,.25), (40,1),
              
              (45,.25), (47,.5), ('R',.25), (47,.5), (55,.25), (54,.25), (52,.25), (50, .25), ('R', .25), (50,.125), (52, .125), (54, .125), (52, .125), (47, .25), (49, .5),
              
              (45,.25), (47,.5), ('R',.25), (47,.5), (55,.25), (54,.25), (52,.25), (50, .25), (57, .5), (52, 1),
              
              (45,.25), (47,.5), ('R',.25), (47,.5), (55,.25), (54,.25), (52,.25), (50, .25), ('R', .25), (50,.125), (52, .125), (54, .125), (52, .125), (47, .25), (49, .5),

              (45,.25), ('R',.25), (45,.25), (50,.25), (48,.25), (46,.25), (45,.25), (43,.25), (41,.25), (40,.25), (38,.25), (45,1), (38,.125)
    ]

    return notes

def main(argv=None):
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--infile", help="path to a musicXML file")

    args = parser.parse_args()

    notes = None

    if(args.infile):
        music_xml = musicxml_parse_test.mxl_container(args.infile)
        notearray = music_xml.get_note_array()
        notes = make_notes_from_notearray(notearray)

    else:
        notes = get_default_notes()

    #44.1KHz is actually kind of pushing it, so do half that.
    sample_rate = 22050

    #Open the audio interface
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=sample_rate,
                    output=True)
    #And play!
    for note in notes:
        
        #slapdash way to implement rests.
        if(note[0] == 'R'):
            print 'R'
            time.sleep(note[1])
            continue

        hertzen = key_to_freq(note[0])
        print hertzen
        test_osc = data_provider.multi_oscillator(hertzen, sample_rate_in_hz=sample_rate, volume = .1, chunksize=1)
        
        starttime = time.clock()

        #Hold each note for a second
        while((time.clock() - starttime) < note[1]):
            data = test_osc.get_data()
            data_struct = struct.pack('f'*len(data), *data)
            data_buffer = buffer(data_struct)
            stream.write(data_buffer)

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main())
