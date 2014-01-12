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

import numpy as np

import time

def key_to_freq(key):
    # Derived from https://en.wikipedia.org/wiki/Piano_key_frequencies
    #
    # Key 1 is A0, key 88 is C8
    print key

    num_harmonics = 4

    twelfth_root_of_two = np.power(2, float(1)/12)
    freq = (np.power(twelfth_root_of_two, (key - 49)) * 440)

    freq_array = []

    #Odd harmonics are woodwind-esque.
    for x in range(1, (num_harmonics * 2) + 1, 2):
        freq_array.append(freq * x)
    
    return freq_array

def main(argv=None):

    #Define an oscillator

    #hz_array = [x * 440 for x in range(1,4)]
    #print hz_array
    #sample_rate = 44100  #CD quality sine waves.

    #44.1KHz is actually kind of pushing it.
    sample_rate = 22050

    #First couple notes of Also Sprach Zarathustra.
    #format is: (piano_key_#, duration (seconds-ish))
    notes = [(40,1),(47,1),(52,1),(44,.25),(43,2)]

    #Open the audio interface
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=sample_rate,
                    output=True)
    #And play!
    for note in notes:
        hertzen = key_to_freq(note[0])
        print hertzen
        test_osc = data_provider.multi_oscillator(hertzen, sample_rate_in_hz=sample_rate, volume = .1)
        
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
