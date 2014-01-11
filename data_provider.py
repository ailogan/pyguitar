# data_provider.py
#
# Andrew Logan - 1/7/2014
# 
# A handful of data sources that can be used to generate audio data with specific characteristics.
#
# TODO: A less generic name would be nice.
# TODO: ADSR FTW

import pyaudio
import numpy as np
import scipy

from scipy import pi

class data_provider:
    """a class that wraps fairly generic audio providers.  Essentially entirely virtual."""
    chunksize = None
    sample_rate_in_hz = None

    def __init__(self):
        raise NotImplementedError()

    def get_data(self):
        """return a chunksize length array of 16-bit ints suitable for feeding into the FFT function."""
        raise NotImplementedError()

#And here are a handful of classes that extend that interface.

#quickie "don't do anything" data_provider.
#TODO: Would be interesting to 
class null_provider(data_provider):
    chunksize = 1024
    sample_rate_in_hz = 1
    
    def __init__(self):
        pass

    def get_data(self):
        return map(lambda x: 0, range(0, self.chunksize))

#a generic sine wave oscillator.
#TODO: Maybe interesting to provide a couple of waveform functions as well?  sine, sawtooth, square?
class oscillator(data_provider):
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
        
        #And sample the sine wave!
        for x in range(0, self.chunksize):
            chunk.append(10 * scipy.sin(2 * pi * self.hertz * (float(self.current_pos) / self.sample_rate_in_hz)))
            self.current_pos = self.current_pos + 1
            self.current_pos = self.current_pos % self.sample_rate_in_hz
            
        return chunk

#multiball!
#TODO: make this a wrapper around the oscillator class
class multi_oscillator(data_provider):
    hertzen = None
    chunksize = None
    sample_rate_in_hz = None
    current_pos = None

    def __init__(self, hertzen):
        self.hertzen = hertzen
        self.chunksize = 1024
        self.current_pos = 0
        max_freq = max(hertzen)
        self.sample_rate_in_hz = int(np.ceil(max_freq * 2 + (.001 * max_freq))) #You know what?  Let's try out the Nyquist-Shannon sampling theorem.  (In order to be uniquly identifiable the frequency has to be less than .5 the sampling frequency)

    def get_data(self):
        chunk = []
        
        #And sample the sine waves!
        for x in range(0, self.chunksize):
            value = 0
            for hertz in self.hertzen:
                value += scipy.sin(2 * pi * hertz * (float(self.current_pos) / self.sample_rate_in_hz))

            chunk.append(value)
            self.current_pos = self.current_pos + 1
            
        return chunk

class audio_input(data_provider):
    chunksize = None
    sample_rate_in_hz = None
    p = None
    inStream = None

    def __init__(self, sample_rate):
        self.sample_rate_in_hz = sample_rate
        self.chunksize = 1024 #I guess?  I'm not sure it matters.

        self.p = pyaudio.PyAudio() 
        self.inStream = p.open(format=pyaudio.paInt16,
                               channels=1,
                               rate=input_rate,
        input=True)

    def get_data(self):
        data = numpy.fromstring(inStream.read(chunksize), dtype=numpy.int16)
        return data
