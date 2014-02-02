#!/opt/local/bin/python2.7

# pyguitar.py
#
# Andrew Logan - 1/12/14
#
# Program written as a guitar practice aid.  Should eventually pull in a midi file and see if the guitar has hit essentially the right note at essentially the right time.  Pulling in pygame in order to show the notes as they're arriving.

import data_provider
import freq_analyze

import argparse

import pygame
import threading

import sys

import copy

import numpy as np



#Shared between threads
data = None
data_lock = None

def crank_fft(fa):
    global data, data_lock
    previous_intensity = 0

    clk = pygame.time.Clock()

    while True:
        #Get some data out of the provider
        num_notes = 1
        analysis_results = fa.iterate(num_notes)

        freq = 0.0
        intensity = 0.0
        note = None

        if(len(analysis_results) != 0):
            freq = analysis_results[0][0]
            intensity = analysis_results[0][1]
            note = analysis_results[0][2][2]
    
        intensity_delta = (intensity - previous_intensity)
        previous_intensity = intensity

        print "freq: {0:9.2f} intensity: {1:13.2f} (delta: {2:13.2f}) note: {3:3s}".format(freq, intensity, intensity_delta, note)
    
        #and collect the data for the spectrogram window
        fft_y = copy.deepcopy(fa.get_raw_fft_output())
    
        #Chop off the high-frequency notes that don't fit in the window
        #fft_scale_factor = fftsize / float(len(data[-1]))
        fft_scale_factor = len(fft_y) / len(data[-1])
    
        fft_y=abs(fft_y[0:(len(fft_y)/fft_scale_factor)]) / (500 * 100) #This does a lot.  Throw out the second half of the FFT result (because they're negative frequencies?), remove the complex part of the FFT result and then scale the results to stay within 0-256.
        
        for i in range(len(fft_y)):
            if fft_y[i]<0: fft_y[i]=0

        with data_lock:
            data=np.roll(data,-1,0)
            data[-1]=fft_y[::-1]

        #limit the rate we update at to save some CPU (20Hz should be fine)
        clk.tick(20)

def positive_int(string):
    num = int(string)
    if (num <= 0):
        raise argparse.ArgumentTypeMessage("need to provide a positive number!")
    
    return num

def main(argv=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--infile", help="path to a wav file")
    parser.add_argument("--wx", help="window width" , default=1024, type=positive_int)
    parser.add_argument("--wy", help="window height", default=1024, type=positive_int)

    args = parser.parse_args()

    windowWidth  = args.wx
    windowHeight = args.wy

    #Start pygame
    pygame.init()

    #Set up the display
    pygame.display.set_caption("Spectrograph test")
    screen = pygame.display.set_mode((windowWidth, windowHeight))
    world = pygame.Surface((windowWidth, windowHeight), depth=8)

    #Choose a palette
    palette = [(0,0,x) for x in range(0,256)]
    world.set_palette(palette)

    data_prov = None

    #Set up the analyzer
    if(args.infile):
        data_prov = data_provider.wav_file(args.infile, chunksize=1024, repeat=True, play=True)

    else:
        sample_rate = 44100
        data_prov = data_provider.audio_input(sample_rate)

    fa = freq_analyze.freq_analyze(data_prov)
    
    clk = pygame.time.Clock()

    global data, data_lock

    #Initialize the data array to be all zeros.
    data=np.array(np.zeros((windowWidth,windowHeight)),dtype=int)

    #Initialize the lock object
    data_lock = threading.Lock()

    #And give it to the data collection thread.
    input_thread = threading.Thread(target=crank_fft, args=[fa])

    #Make the thread quit when the program quits
    input_thread.daemon = True

    #launch thread!
    input_thread.start()

    while True:
        #pygame event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        #Expecting that the fft thread wil keep updating the data array asynchronously.
        
        with data_lock:
            pygame.surfarray.blit_array(world,data) #data into window

        screen.blit(world, (0,0))
        pygame.display.flip() #render window
        clk.tick(30) #limit to 30FPS

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main(sys.argv))
