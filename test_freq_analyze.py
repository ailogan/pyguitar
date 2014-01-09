# test_freq_analyze.py
#
# Andrew Logan - 1/8/2014
# 
# Unit tests for the freq_analyze class.

import unittest
import freq_analyze

import pyaudio
import wave
import sys

class fft_test(unittest.TestCase):
    def test_freq_to_key(self):
        fa = freq_analyze.freq_analyze(0,0)
        
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

        p = pyaudio.PyAudio()

        wf = wave.open("Sine_wave_440.wav", 'rb')
    
        rate = wf.getframerate()
   
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=rate,
                        output=True)

        chunksize = 1024
        num_frames = 8
        fft_buffer_size = num_frames*chunksize
        
        fa = freq_analyze.freq_analyze(fft_buffer_size, rate)

        #Add enough chunks that we throw away some data.
        for x in range(0, num_frames + 2):
            data = wf.readframes(chunksize)

            fa.add_data(data)

            if(((x+1) * chunksize) < fft_buffer_size):
                self.assertEqual(len(fa.fft_input_buffer), (x+1) * chunksize)

            else:
                self.assertEqual(len(fa.fft_input_buffer), fft_buffer_size)


        analysis_results = fa.get_frequencies(1)

        freq_in_hertz = analysis_results[0][0]

        #Make sure that the frequency we grabbed is fairly close to what it should be
        print "freq_in_hertz: " + str(freq_in_hertz)
        self.assertTrue(freq_in_hertz > 439)
        self.assertTrue(freq_in_hertz < 441)

        #Should also be the right note
        self.assertEqual(analysis_results[0][2], "A4")
        

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    unittest.main()
