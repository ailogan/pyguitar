# data_provider.py
#
# Andrew Logan - 1/7/2014
# 
# A handful of data sources that can be used to generate audio data with specific characteristics.
#
# TODO: A less generic name would be nice.
# TODO: ADSR FTW

import cProfile

import pyaudio
import wave

import numpy as np

import math
from math import pi

#Winds up being incredibly slower than just calling math.sin()
#import scipy
#from scipy import pi


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
    volume = None
    tau = 2 * pi

    def __init__(self, hertz, sample_rate_in_hz = None, volume = 1, chunksize=1024):
        self.hertz = hertz
        self.current_pos = 0.0

        self.chunksize = chunksize

        self.volume = volume

        #Calculate the sample rate if it wasn't passed in as an argument
        if(not sample_rate_in_hz):
            self.sample_rate_in_hz = int(math.ceil(hertz * 2 + (.001 * hertz))) #You know what?  Let's try out the Nyquist-Shannon sampling theorem.  (In order to be uniquly identifiable the frequency has to be less than .5 the sampling frequency)

        else:
            self.sample_rate_in_hz = sample_rate_in_hz

    def get_data(self):
        chunk = []
        
        #And sample the sine wave!
        for x in range(0, self.chunksize):
            chunk.append(self.volume * math.sin(self.tau * self.hertz * (self.current_pos / self.sample_rate_in_hz)))
            self.current_pos = self.current_pos + 1
            
            #Meh.
            #self.current_pos = self.current_pos % self.sample_rate_in_hz
            
        return chunk

#multiball!
#TODO: make this a wrapper around the oscillator class
class multi_oscillator(data_provider):
    hertzen = None
    chunksize = None
    volume = None
    sample_rate_in_hz = None
    current_pos = None
    oscillators = None

    #Save time by calculating this up front
    tau = 2 * pi

    def __init__(self, hertzen, sample_rate_in_hz=None, volume = 1, chunksize=1024):
        self.hertzen = hertzen

        self.chunksize = chunksize

        self.volume = volume
        
        self.oscillators = []

        #Save time by declaring this a float at the start rather than casting it later
        self.current_pos = 0.0

        #calculate an appropriate rate if we're not trying to force a particular sample rate
        if(not sample_rate_in_hz):
            max_freq = max(hertzen)
            self.sample_rate_in_hz = int(math.ceil(max_freq * 2 + (.001 * max_freq))) #You know what?  Let's try out the Nyquist-Shannon sampling theorem.  (In order to be uniquly identifiable the frequency has to be less than .5 the sampling frequency)

        else:
            self.sample_rate_in_hz = sample_rate_in_hz

        for hz in hertzen:
            #These all have to be the same sample rate and chunksize because we're going to be merging them together later
            self.oscillators.append(oscillator(hz, sample_rate_in_hz = self.sample_rate_in_hz, volume = self.volume, chunksize = self.chunksize))

    #Maybe this will keep it from popping so much when notes change?
    def update(self, hertzen):
        self.hertzen = hertzen

    def get_data(self):
        #initialize the chunk array
        chunk = []

        #And sample the sine waves!
        for x in range(0, self.chunksize):
            value = 0
            for hertz in self.hertzen:
                #It would be great if this could be sped up even more
                value += (self.volume * math.sin(self.tau * hertz * (self.current_pos / self.sample_rate_in_hz)))

            chunk.append(value)
            self.current_pos = self.current_pos + 1

        return chunk

#         #Seed the result array with a bunch of zeros
#         chunk = [0 for x in range(0, self.chunksize)]
#         
#         #Gather data and merge it all together
#         for osc in self.oscillators:
#             osc_array = osc.get_data()
#             
#             #There's got to be a cleaner way to do this.
#             for x in range(0,len(chunk)):
#                 chunk[x] += osc_array[x]
# 
#         return chunk

class audio_input(data_provider):
    chunksize = None
    sample_rate_in_hz = None
    p = None
    inStream = None

    def __init__(self, sample_rate, chunksize=1024):
        self.sample_rate_in_hz = sample_rate
        self.chunksize = chunksize

        self.p = pyaudio.PyAudio() 
        self.inStream = self.p.open(format=pyaudio.paInt16,
                                    channels=1, #Mono is good enough
                                    rate=self.sample_rate_in_hz,
                                    input=True)

    def get_data(self):
        pcm = np.fromstring(self.inStream.read(self.chunksize), dtype=np.int16)
        return pcm

class wav_file(data_provider):
    chunksize = None
    sample_rate_in_hz = None

    num_channels = None
    repeat = None
    p = None
    wf = None

    stream = None

    def __init__(self, filename, chunksize=1024, repeat=False, play=False):
        self.repeat = repeat
        self.chunksize = chunksize

        self.p = pyaudio.PyAudio()

        self.wf = wave.open(filename, 'rb')

        self.num_channels = self.wf.getnchannels()

        if(self.num_channels != 1):
            raise Exception("only mono files are supported")

        self.sample_rate_in_hz = self.wf.getframerate()

        if(play):
            self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                                      channels=self.num_channels,
                                      rate=self.sample_rate_in_hz,
                                      output=True)

    #TODO: How do I mix a file down to mono?  The FFT routines aren't expecting stereo files.
    def get_data(self):
        data = self.wf.readframes(self.chunksize)

        #Rewind at the end of the file if the repeat flag is set.
        if((self.repeat == True) and
           (len(data) != self.chunksize * self.num_channels * 2)):
            #Hit the end of the file, so run it back to the beginning and try it again
            #TODO: can probably do this a lot better.
            print "Rewinding!"
            self.wf.rewind()
            data = self.wf.readframes(self.chunksize)

        if(self.stream):
            self.stream.write(data)

        pcm=np.fromstring(data, dtype=np.int16)

        return pcm
