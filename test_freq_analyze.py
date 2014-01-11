# test_freq_analyze.py
#
# Andrew Logan - 1/8/2014
# 
# Unit tests for the freq_analyze class.

import unittest
import freq_analyze

import pyaudio

import scipy
from scipy import pi

import numpy as np

import sys

#quickie "don't do anything" data_provider.
class null_provider(freq_analyze.data_provider):
    chunksize = 1024
    sample_rate_in_hz = 1
    
    def __init__(self):
        pass

    def get_data(self):
        return map(lambda x: 0, range(0, self.chunksize))

#a generic sine wave oscillator
class oscillator(freq_analyze.data_provider):
    hertz = None
    chunksize = None
    sample_rate_in_hz = None
    current_pos = None

    def __init__(self, hertz):
        self.hertz = hertz
        self.chunksize = 1024
        self.current_pos = 0
        self.sample_rate_in_hz = int(np.ceil(hertz * 2 + (.001 * hertz))) #You know what?  Let's try out the Nyquist-Shannon sampling theorem.  (In order to be uniquly identifiable the frequency has to be less than .5 the sampling frequency)

    def get_data(self):
        chunk = []
        
        #Divide the chunk into hundreths of a radian.  The good news is that sine waves are at least periodic.
        for x in range(0, self.chunksize):
            chunk.append(10 * scipy.sin(2 * pi * self.hertz * (float(self.current_pos) / self.sample_rate_in_hz)))
            self.current_pos = self.current_pos + 1
            self.current_pos = self.current_pos % self.sample_rate_in_hz
            
        return chunk

class fft_test(unittest.TestCase):
    def test_freq_to_key(self):
        fa = freq_analyze.freq_analyze(null_provider)
        
        #Test two full octaves
        self.assertEqual(fa.freq_to_key(65.41), "C2")
        self.assertEqual(fa.freq_to_key(69.30), "C#2")
        self.assertEqual(fa.freq_to_key(73.42), "D2")
        self.assertEqual(fa.freq_to_key(77.78), "D#2")
        self.assertEqual(fa.freq_to_key(82.41), "E2")
        self.assertEqual(fa.freq_to_key(87.31), "F2")
        self.assertEqual(fa.freq_to_key(92.50), "F#2")
        self.assertEqual(fa.freq_to_key(98.00), "G2")
        self.assertEqual(fa.freq_to_key(103.8), "G#2")
        self.assertEqual(fa.freq_to_key(110.0), "A2")
        self.assertEqual(fa.freq_to_key(116.5), "A#2")
        self.assertEqual(fa.freq_to_key(123.5), "B2")

        self.assertEqual(fa.freq_to_key(130.8), "C3")
        self.assertEqual(fa.freq_to_key(138.6), "C#3")
        self.assertEqual(fa.freq_to_key(146.8), "D3")
        self.assertEqual(fa.freq_to_key(155.6), "D#3")
        self.assertEqual(fa.freq_to_key(164.8), "E3")
        self.assertEqual(fa.freq_to_key(174.6), "F3")
        self.assertEqual(fa.freq_to_key(185.0), "F#3")
        self.assertEqual(fa.freq_to_key(196.0), "G3")
        self.assertEqual(fa.freq_to_key(207.7), "G#3")
        self.assertEqual(fa.freq_to_key(220.0), "A3")
        self.assertEqual(fa.freq_to_key(233.1), "A#3")
        self.assertEqual(fa.freq_to_key(246.9), "B3")

        #Standard guitar tuning
        self.assertEqual(fa.freq_to_key(82.41), "E2")
        self.assertEqual(fa.freq_to_key(110)  , "A2")
        self.assertEqual(fa.freq_to_key(146.8), "D3")
        self.assertEqual(fa.freq_to_key(196)  , "G3")
        self.assertEqual(fa.freq_to_key(246.9), "B3")
        self.assertEqual(fa.freq_to_key(329.6), "E4")

        #piano
        self.assertEqual(fa.freq_to_key(27.5) , "A0")
        self.assertEqual(fa.freq_to_key(4186) , "C8")

        #All of the octaves
        self.assertEqual(fa.freq_to_key(16.35), "C0")
        self.assertEqual(fa.freq_to_key(32.70), "C1")
        self.assertEqual(fa.freq_to_key(65.41), "C2")
        self.assertEqual(fa.freq_to_key(130.8), "C3")
        self.assertEqual(fa.freq_to_key(261.6), "C4")
        self.assertEqual(fa.freq_to_key(523.3), "C5")
        self.assertEqual(fa.freq_to_key(1047) , "C6")
        self.assertEqual(fa.freq_to_key(2093) , "C7")
        self.assertEqual(fa.freq_to_key(4186) , "C8")

    def test_get_freqencies(self):
        print

        for x in range(1, 30000, 50):
            test_osc = oscillator(x)

            fa = freq_analyze.freq_analyze(test_osc)

            analysis_results = fa.iterate(1)

            freq_in_hertz = analysis_results[0][0]
            freq_as_note  = analysis_results[0][2]

            #Make sure that the frequency we grabbed is within 1% of what it should be
            print "freq_in_hertz: " + str(freq_in_hertz)
            self.assertTrue(freq_in_hertz > (x - (.01 * x)))
            self.assertTrue(freq_in_hertz < (x + (.01 * x)))
            

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    unittest.main()
