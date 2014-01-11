# freq_analyze.py
#
# Andrew Logan - 1/8/2014
# 
# Library that provides a class that takes in audio input, runs it through a Fourier transform and produces an array of tuples of frequency, intensity and music note.

import numpy as np
import scipy
import scipy.fftpack

class data_provider:
    """a class that provides audio input to the frequency analyzer.  Essentially entirely virtual."""
    chunksize = None
    sample_rate_in_hz = None

    def __init__(self):
        raise NotImplementedError()

    def get_data(self):
        """return a chunksize length array of 16-bit ints suitable for feeding into the FFT function."""
        raise NotImplementedError()

class freq_analyze:
    """a class that takes in input from a data_provider class, runs it through a Fourier transform and produces an array of tuples of frequency, intensity and music note."""

    data_provider = None

    fft_input_buffer = None
    fft_input_buffer_size = None  #The idea is that we get a much more accurate FFT result if we have a bigger input window.
    sample_rate = None

    def __init__(self, data_provider):
        self.data_provider = data_provider

        self.fft_input_buffer = []
        self.fft_input_buffer_size = 8 * self.data_provider.chunksize  #Not super-thrilled about this layout.
        self.sample_rate = self.data_provider.sample_rate_in_hz

    def __add_data(self, pcm_data):
        self.fft_input_buffer.extend(pcm_data)

        #Make sure the buffer doesn't get too big
        self.fft_input_buffer = self.fft_input_buffer[-self.fft_input_buffer_size:]

    #Throw away the accumulated buffer
    def clear(self):
        self.fft_input_buffer = []
        
    #This isn't perfect on real instruments.  See https://en.wikipedia.org/wiki/Railsback_curve#The_Railsback_curve for more about that.
    def freq_to_key(self, freq_in_hertz):
        # Derived from https://en.wikipedia.org/wiki/Piano_key_frequencies
        #
        # Key 1 is A0, key 88 is C8

        keynum = int(np.around(12 * np.log2(float(freq_in_hertz) / 440) + 49)) #Because A4 (440Hz) is the reference and the 49th key.  Round to the nearest whole number to allow for a bit of slop.

        #There are three notes in the lowest octave, so add 8 to make it an even 11 and then divide by 12 to get the octave.
        octave = ((keynum + 8) / 12)
    
        notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
        
        #A is 1, so shift everything down by 1 to make it 0.
        note_idx = ((keynum - 1) % 12) 
        
        note_name = notes[note_idx] + str(octave)
        
        return note_name
    
    def iterate(self, num_frequencies):
        #Take our data and convert it into a collection of frequencies.  The return value is:
        # Discrete Fourier transform of a real sequence.
        #
        # The returned real arrays contains:
        #
        # [y(0),Re(y(1)),Im(y(1)),...,Re(y(n/2))]              if n is even
        # [y(0),Re(y(1)),Im(y(1)),...,Re(y(n/2)),Im(y(n/2))]   if n is odd
        #
        # where
        #
        # y(j) = sum[k=0..n-1] x[k] * exp(-sqrt(-1)*j*k*2*pi/n)
        # j = 0..n-1
        #
        # Note that y(-j) == y(n-j).conjugate().

        #Fill the buffer, but get at least one additional chunk
        for x in range(1, (self.fft_input_buffer_size / self.data_provider.chunksize) + 1):
            #Get more data
            self.fft_input_buffer.extend(self.data_provider.get_data())

            #Make sure the buffer doesn't get too big
            self.fft_input_buffer = self.fft_input_buffer[-self.fft_input_buffer_size:]

        #Do the Fourier transform
        fft_y=abs(scipy.fftpack.fft(self.fft_input_buffer))

        # Cut the ffty array in half to avoid having to process duplicate values.
        # (the second half of the array contains the negative solutions, which don't interest me)
        positive_fft_y = fft_y[0:len(fft_y)/2]

        #But we need to convert the original array to a set of frequencies, otherwise there's a chunk of energy that's missing from the frequency analysis.  The docs say:

        #"The returned float array f contains the frequency bin centers in cycles per unit of the sample spacing (with zero at the start). For instance, if the sample spacing is in seconds, then the frequency unit is cycles/second."
        freqs = np.fft.fftfreq(len(fft_y)) 

        #Order the indexes of the positive FFT results by intensity.
        sorted_positive_fft_y = np.argsort(positive_fft_y**2)

        result = []

        #And assemble the result!
        for x in sorted_positive_fft_y[-1:-(num_frequencies+1):-1]:
            intensity = float(abs(positive_fft_y[x])) #Might one day be interesting to figure out the units here.  Or at least the range of possible values.
            freq = freqs[x]
            freq_in_hertz = abs(freq*self.sample_rate)
            key = self.freq_to_key(freq_in_hertz)

            result.append([freq_in_hertz, intensity, key])

            # print "frequency: {0:10.2f} Hz (intensity: {1:12.3f}) note: {2:s}".format(float(freq_in_hertz), intensity, key)
            
        return result
