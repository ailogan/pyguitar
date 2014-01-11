# test_freq_analyze.py
#
# Andrew Logan - 1/8/2014
# 
# Unit tests for the freq_analyze class.

import unittest
import freq_analyze
import data_provider

import pyaudio

import scipy
from scipy import pi

import numpy as np

import sys

import time  #For sleep()

from itertools import chain, combinations

#See if a test frequency is reasonably close to a reference freqency
def within_tolerance(test_frequency, reference_frequency, tolerance, print_notes=False):
    if(print_notes):
        print "test_frequency: {0:9.2f}Hz reference_frequency: {1:9.2f}Hz tolerance: +/- {2:9.2f}Hz".format(test_frequency, reference_frequency, tolerance)

    if((test_frequency <= (reference_frequency + tolerance)) and
       (test_frequency >= (reference_frequency - tolerance))):
        return True

    return False

class fft_test(unittest.TestCase):
    def test_freq_to_key(self):
        fa = freq_analyze.freq_analyze(data_provider.null_provider)
        
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

    def test_freqencies(self):
        print
        print "Testing single oscillator"
        
        #https://oeis.org/A051109 (hyperinflation series for banknotes, but an interesting collection of numbers regardless)
        for x in [ ((n % 3) ** 2 + 1) * 10**int(n/3) for n in range(15)]:
            test_osc = data_provider.oscillator(x)

            fa = freq_analyze.freq_analyze(test_osc)

            analysis_results = fa.iterate(1)

            freq_in_hertz = analysis_results[0][0]

            #Make sure that the frequency we grabbed is within 1% of what it should be
            self.assertTrue(within_tolerance(freq_in_hertz, x, (.01 *x), print_notes=True))
            
    def test_multiple_frequencies(self):
        print
        print "Testing multiple oscillators"

        #The frequencies we want to test
        #These are a couple of prime numbers.  Also, it turns out that the FFT isn't great at really low freqencies (eg: 11 Hz) paired with really high frequencies (eg: 20KHz)
        base_freqs = [29, 349, 1013, 4583, 10271, 25097]

        #Now iterate over all of the combinations (via https://stackoverflow.com/questions/464864/python-code-to-pick-out-all-possible-combinations-from-a-list)
        #(roughly: use map to make combinations of every relevant length and then use chain to turn the generators into something we can iterate over.  Also, skip the null set.
        for freqs in chain(*map(lambda x: combinations(base_freqs, x), range(1, len(base_freqs)+1))):

            test_osc = data_provider.multi_oscillator(freqs)

            fa = freq_analyze.freq_analyze(test_osc)
            
            analysis_results = fa.iterate(len(freqs))

            result_freqs = []
            for x in range(0, len(freqs)):
                #these come back in power order, not note order
                result_freqs.append(analysis_results[x][0])

            result_freqs = np.sort(result_freqs)

            for x in range(0, len(freqs)):
                result_freq = result_freqs[x]
                test_freq = freqs[x]
                
                #Make sure that the frequencies we grabbed are within 5Hz of what they should be.
                self.assertTrue(within_tolerance(result_freq, test_freq, 5, print_notes=True))

            print "======="

    def test_wav_file(self):
        print
        print "Opening wav file"
        
        filename = "Sine_wave_440.wav"

        A440_test = data_provider.wav_file(filename, repeat=True)
        reference_freq = 440

        fa = freq_analyze.freq_analyze(A440_test)

        #Eh, try it a bunch of times.
        for samples in range(0, 50):
            analysis_results = fa.iterate(1)

            result_freq = analysis_results[0][0]
            
            #See if it's within 1Hz of 440Hz
            self.assertTrue(within_tolerance(result_freq, reference_freq, 1, print_notes=True))

    def test_audio_input(self):
        print
        print "testing audio input"

        sample_rate = 44100 #CD quality is good enough.

        audio_in = data_provider.audio_input(sample_rate)

        fa = freq_analyze.freq_analyze(audio_in)

        #Wait a bit, since it's sort of a weird test to make the user provide input at a known frequency.
        
        for x in range(0,50):
            num_notes = 6
            analysis_results = fa.iterate(num_notes)
            
            freqs = []

            for y in range(0, num_notes):
                print "freq: {0:9.2f}".format(analysis_results[y][0]),

            print

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    unittest.main()
