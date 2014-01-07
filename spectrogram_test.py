#!/usr/bin/python

#Based off of the spectrogram example from http://www.swharden.com/blog/2010-06-19-simple-python-spectrograph-with-pygame and the pyaudio example source (http://people.csail.mit.edu/hubert/pyaudio/#examples)

import argparse

import pygame

import threading

import pyaudio
import wave

import sys

import numpy
import scipy
import scipy.fftpack
import scipy.io.wavfile

data = None #Shared between threads
currentCol = 0 #Because python doesn't really do static variables
scooter = [] #Ditto

#constants
windowWidth  = 1024
fftsize = 2048

#Dunno what this is.
overlap = 1 #1 for raw, realtime - 8 or 16 for high-definition

#This isn't perfect on real instruments.  See https://en.wikipedia.org/wiki/Railsback_curve#The_Railsback_curve for more about that.
def freq_to_key(freq_in_hertz):
    # Derived from https://en.wikipedia.org/wiki/Piano_key_frequencies
    #
    # Key 1 is A0, key 88 is C8

    keynum = int(numpy.around(12 * numpy.log2(freq_in_hertz / 440) + 49)) #Because A4 (440Hz) is the reference and the 49th key.  Round to the nearest whole number to allow for a bit of slop.


    #There are three notes in the lowest octave, so add 9 to make it an even 12 and then divide by 12 to get the octave.
    octave = ((keynum + 9) / 12)
    
    notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

    #A is 1, so shift everything down by 1 to make it 0.
    note_idx = ((keynum - 1) % 12) 

    note_name = notes[note_idx] + str(octave)

    return note_name

def graphFFT(pcm, frate):
        global currentCol, data
        
        #Take the PCM data and convert it into a collection of frequencies.  The data is:
        # "
        # The returned complex array contains y(0), y(1),..., y(n-1) where
        # y(j) = (x * exp(-2*pi*sqrt(-1)*j*np.arange(n)/n)).sum().
        # "

        ffty=scipy.fftpack.fft(pcm)

        #And covert that into a set of frequencies.  The format is:

        #"The returned float array f contains the frequency bin centers in cycles per unit of the sample spacing (with zero at the start). For instance, if the sample spacing is in seconds, then the frequency unit is cycles/second."
        freqs = numpy.fft.fftfreq(len(ffty)) 
 
        # Find the peak in the coefficients
        idx = numpy.argmax(numpy.abs(ffty)**2)  #TODO: Why square it?
        intensity = float(abs(ffty[idx]))
        
        #Again, a totally arbitrary cutoff
        if(intensity > 100000):

           freq = freqs[idx]
           freq_in_hertz = abs(freq*frate)
           if(freq_in_hertz > 1):
               key = freq_to_key(freq_in_hertz)
               print "dominant frequency: {0:10.2f} Hz (intensity: {1:12.3f}) note: {2:s}".format(float(freq_in_hertz), intensity, key)
         
        #and now display this on the screen

        ffty=abs(ffty[0:len(ffty)/2]) / (500 * 100) #This does a lot.  Throw out the second half of the FFT result (because they're negative frequencies?), remove the complex part of the FFT result and then scale the results to stay within 0-256.
        #ffty=(scipy.log(ffty))*30-50 # if you want uniform data
        #print "MIN:\t%s\tMAX:\t%s"%(min(ffty),max(ffty))
        for i in range(len(ffty)):
                if ffty[i]<0: ffty[i]=0

                #Meh.  Pick an arbitrary precision and display everything bigger than that.
                # if(ffty[i] > 150): print " " + str(i) + ": " + str(ffty[i]),
                
        scooter.append(ffty)
        if len(scooter)<6:return
        scooter.pop(0)
        ffty=(scooter[0]+scooter[1]*2+scooter[2]*3+scooter[3]*2+scooter[4])/9 #some sort of a weighted average of historical data?
        data=numpy.roll(data,-1,0)
        data[-1]=ffty[::-1]
        currentCol+=1
        if currentCol==windowWidth: currentCol=0

def record():
    input_rate = 44100

    p = pyaudio.PyAudio() 
    inStream = p.open(format=pyaudio.paInt16,
                      channels=1,
                      rate=input_rate,
                      input=True)

    linear=[0]*fftsize
    while True:
        linear=linear[fftsize/overlap:]
        pcm=numpy.fromstring(inStream.read(fftsize/overlap), dtype=numpy.int16)
        linear=numpy.append(linear,pcm)
        graphFFT(linear, input_rate)


def play_file(filename):
    p = pyaudio.PyAudio()

    wf = wave.open(filename, 'rb')
    # wf = wave.open("C_major_scale_mono.wav", 'rb')
    
    rate = wf.getframerate()
    
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=rate,
                    output=True)

    linear=[0]*fftsize
    chunksize = fftsize/overlap
    num_channels = wf.getnchannels()

    while True:
        data = wf.readframes(chunksize)

        if(len(data) != chunksize * num_channels * 2):
            #Hit the end of the file, so run it back to the beginning and try it again
            #TODO: can probably do this a lot better.
            print "Rewinding!"
            wf.rewind()
            data = wf.readframes(chunksize)

        #Play what we read from the wav file
        stream.write(data)

        linear=linear[chunksize:]
        pcm=numpy.fromstring(data, dtype=numpy.int16)
        linear=numpy.append(linear,pcm)
        graphFFT(linear, rate)

def main(argv=None):
    global data

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--infile", help="path to a wav file")

    args = parser.parse_args()
    
    pygame.init() #crank up PyGame

    pygame.display.set_caption("Simple Spectrograph")
    screen=pygame.display.set_mode((windowWidth,fftsize/2))
    world=pygame.Surface((windowWidth,fftsize/2),depth=8) # MAIN SURFACE

    pal = [(max((x-128)*2,0),x,min(x*2,255)) for x in xrange(256)] 
    print max(pal),min(pal)

    world.set_palette(pal)

    #Initialize the data array to be all zeros.  It will be updated asynchronously by the recording thread.
    data=numpy.array(numpy.zeros((windowWidth,fftsize/2)),dtype=int)

    input_thread = None

    if(args.infile != None):
        input_thread=threading.Thread(target=play_file, args=[args.infile]) #Use canned input

    else:
        input_thread=threading.Thread(target=record) #Start the recording thread instead.

    input_thread.daemon=True # daemon mode forces thread to quit with program
    input_thread.start() #launch thread

    clk=pygame.time.Clock()

    while True:
        #pygame event loop
        for event in pygame.event.get(): #check if we need to exit
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.surfarray.blit_array(world,data) #place data in window
        screen.blit(world, (0,0))
        pygame.display.flip() #RENDER WINDOW
        clk.tick(30) #limit to 30FPS

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main(sys.argv))
