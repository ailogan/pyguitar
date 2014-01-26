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

import numpy as np

import argparse

import time

def key_to_freq(key):
    # Derived from https://en.wikipedia.org/wiki/Piano_key_frequencies
    #
    # Key 1 is A0, key 88 is C8
    #print key

    num_harmonics = 0

    twelfth_root_of_two = np.power(2, float(1)/12)
    freq = (np.power(twelfth_root_of_two, (key - 49)) * 440)

    freq_array = []

    #Fundamental tone
    freq_array.append(freq)

    #Odd harmonics
    for x in range(1, (num_harmonics * 2) + 1, 2):
        freq_array.append(freq * x)

    #Even harmonics
    #for x in range(2, (num_harmonics * 2) +1, 2):
    #    freq_array.append(freq * x)

    #Plucked strings have all of the harmonics, but the odds are louder than the evens.  Let's simulate that by calculating the odd harmonics twice, I guess
    for x in range(1, (num_harmonics + 1)):
        freq_array.append(freq * x)

    return sorted(freq_array)

def make_notes_from_notearray(notearray):
    notes = []
    for note_data in notearray:
        when = note_data[0]
        note = note_data[1]
        duration_in_ms = note_data[2]

        key = ""
        
        #format is: [piano_key_#s], duration_in_seconds]
        
        if(note.step is None):
            key = "R"

        else:
            key = note_to_key(note)
            #print key
            
        #Update the previous entry if this note is in a chord
        if(note.is_chord_member):
            chord_notes = notes[-1][0]
            chord_notes.append(key)

        else:
            duration_in_sec = (duration_in_ms / 1000)
            notes.append([[key], duration_in_sec])

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
        step_num += alter

    #octave -= 1

    #Octaves start at C
    if(step_num > 3):
        octave -= 1

    #And calculate the key number.
    key_num = step_num  + (octave * 12)

    #print "{0}{1} is {2}".format(note.step, note.octave, key_num)

    return key_num

def get_default_notes():
    #First couple notes of Also Sprach Zarathustra.
    #format is: [piano_key_#s], duration_in_seconds]
    #notes = [(40,1),(47,1),(52,1),(44,.25),(43,2)]
    
    #the star wars theme is a fine default.
    notes = [ [[38],1],[[45],1],[[43],.25],[[42],.25],[[40],.25],[[50],1],
              [[45],1],[[43],.25],[[42],.25],[[40],.25],[[50],1],
              [[45],1],[[43],.25],[[42],.25],[[43],.25],[[40],1],
             
             #repeat
              [[38],1],[[45],1],[[43],.25],[[42],.25],[[40],.25],[[50],1],
              [[45],1],[[43],.25],[[42],.25],[[40],.25],[[50],1],
              [[45],1],[[43],.25],[[42],.25],[[43],.25],[[40],1],
              
              [[45],.25],[[47],.5],[['R'],.25],[[47],.5],[[55],.25],[[54],.25],[[52],.25],[[50],.25],[['R'],.25],[[50],.125],[[52],.125],[[54],.125],[[52],.125],[[47],.25],[[49],.5],
              
              [[45],.25],[[47],.5],[['R'],.25],[[47],.5],[[55],.25],[[54],.25],[[52],.25],[[50],.25],[[57],.5],[[52],1],
              
              [[45],.25],[[47],.5],[['R'],.25],[[47],.5],[[55],.25],[[54],.25],[[52],.25],[[50],.25],[['R'],.25],[[50],.125],[[52],.125],[[54],.125],[[52],.125],[[47],.25],[[49],.5],

              [[45],.25],[['R'],.25],[[45],.25],[[50],.25],[[48],.25],[[46],.25],[[45],.25],[[43],.25],[[41],.25],[[40],.25],[[38],.25],[[45],1],[[38],.125]
    ]

    return notes

def main(argv=None):
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--infile", help="path to a musicXML file")

    args = parser.parse_args()

    notes = None

    if(args.infile):
        print "Loading..."
        music_xml = musicxml_parse_test.mxl_container(args.infile)
        notearray = music_xml.get_note_array()
        song = make_notes_from_notearray(notearray)

    else:
        song = get_default_notes()

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
        hertzen = []
        is_rest = False

        for note in notes[0]:
            if (note == 'R'):
                is_rest = True
                continue
            
            hertzen.extend(key_to_freq(note))


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
