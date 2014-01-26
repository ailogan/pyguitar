#!/opt/local/bin/python2.7

# show_notes.py
#
# Andrew Logan - 1/24/14
#
# Program written as a test of displaying a sequence of notes in order.

import sys
import math
import copy
import pygame
import pyaudio
import argparse

import struct
import data_provider
import musicxml_parse_test

import threading

#Shared between threads
hertzen = None
hertzen_lock = None

class SpriteContainer:
    sprite = None
    pos = None
    note = None

    #Sprite is a pygame.Surface object, pos is a tuple containing the x,y coordinates of where the sprite is on screen.

    def __init__(self, sprite, pos, note):
        self.sprite = sprite
        self.pos = pos
        self.note = note
    
    #Moves the sprite some number of pixels from where it is
    def move(self, velocity):
        self.pos[0] += velocity[0]
        self.pos[1] += velocity[1]

def play_tones():
    global hertzen, hertzen_lock

    print "Opening audio device..."

    #44.1KHz is actually kind of pushing it, so do half that.
    sample_rate = 22050

    #Open the audio interface
    p = pyaudio.PyAudio()

    audio_stream = p.open(format=pyaudio.paFloat32,
                          channels=1,
                          rate=sample_rate,
                          output=True)

    previous_hertzen = None
    current_hertzen = None

    with hertzen_lock:
        current_hertzen = copy.deepcopy(hertzen)

    chunksize = 1

    osc = data_provider.multi_oscillator(current_hertzen, sample_rate_in_hz=sample_rate, volume = .1, chunksize=chunksize)
        
    while 1:
        previous_hertzen = current_hertzen
        with hertzen_lock:
            current_hertzen = copy.deepcopy(hertzen)

        #Only update the oscillator if the frequencies have changed.
        if(current_hertzen != previous_hertzen):
            osc = data_provider.multi_oscillator(current_hertzen, sample_rate_in_hz=sample_rate, volume = .1, chunksize=chunksize)

        previous_hertzen = current_hertzen

        data = osc.get_data()
        data_struct = struct.pack('f'*len(data), *data)
        data_buffer = buffer(data_struct)
        audio_stream.write(data_buffer)

def positive_int(string):
    num = int(string)
    if (num <= 0):
        raise argparse.ArgumentTypeMessage("need to provide a positive number!")
    
    return num

def main(argv=None):
    global hertzen, hertzen_lock

    #Get commandline arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--wx", help="window width" , default=640, type=positive_int)
    parser.add_argument("--wy", help="window height", default=480, type=positive_int)

    parser.add_argument("--fps", help="frames per second", default=30, type=positive_int)

    parser.add_argument("--infile", help="path to a musicXML file")

    args = parser.parse_args()

    #Get the dimensions we need
    windowWidth  = args.wx
    windowHeight = args.wy

    fps = args.fps
    
    notearray = []

    if(args.infile):
        print "Loading..."
        music_xml = musicxml_parse_test.mxl_container(args.infile)

        notearray = music_xml.get_note_array()

    #Set up pygame
    pygame.init()
    
    #Make the special buffer that holds the output that's displayed on the screen
    screen = pygame.display.set_mode([windowWidth,windowHeight])
    
    #Load our sample image
    note_sprites = []

    fontobj = pygame.font.Font(None, 50)

    #How quickly the sprites will scroll
    ms_per_pixel = 5

    pixels_per_ms = 1.0 / ms_per_pixel

    #What color they are
    sprite_color = [200,100,0]

    #Subdivide the window so that each string has its own lane
    #TODO: should eventually get the number of strings from the musicXML file
    num_strings = 6
    sprite_height = (windowHeight / num_strings)

    #Start near the right side of the screen
    x_offset = math.ceil(windowWidth * .3)

    for note_data in notearray:
        when = note_data[0]
        note = note_data[1]
        duration_in_ms = note_data[2]

        #Is this a rest?
        if(note.step is None):
            continue

        #pixels = ms * (pixels / ms)
        sprite_width = math.ceil(duration_in_ms * pixels_per_ms)

        sprite = pygame.Surface([sprite_width, sprite_height])
        sprite.fill(sprite_color)
        
        guitar_string = note.string
        guitar_fret   = note.fret

        words = fontobj.render(str(guitar_fret), True, (200,200,200))

        #Put the fret number onto the note sprite
        sprite.blit(words,[0,0])

        #Now we figure out where this is supposed to be.

        start_x_pos = math.ceil(when * pixels_per_ms) + x_offset

        #String 6 (low E) is on the bottom, string 1 (high E) is on the top.  (0,0) is the top left of the screen

        start_y_pos = sprite_height * (guitar_string - 1)

        sprite_container = SpriteContainer(sprite, [start_x_pos, start_y_pos], note)

        note_sprites.append(sprite_container)

    clk=pygame.time.Clock()

    # Whooo unit analysis
    # pixel / frame = (pixel / ms) * (ms / frame)

    ms_per_frame = 1000.0 / fps
    pixels_per_frame = pixels_per_ms * ms_per_frame

    #samples / frame = ((samples / second) / 1000) * (ms / frame)

    line_pos_x = windowWidth * .2

    #Initialize the array
    hertzen = []

    #Initialize the lock object
    hertzen_lock = threading.Lock()

    #And set up the thread responsible for playing tones
    audio_thread = threading.Thread(target=play_tones)

    #Make the thread quit when the program quits
    audio_thread.daemon = True

    #launch thread!
    audio_thread.start()

    previous_hertzen = None
    current_hertzen = []

    while 1:
        for event in pygame.event.get(): #check if we need to exit
                if event.type == pygame.QUIT:pygame.quit();sys.exit()

        previous_hertzen = current_hertzen

        current_hertzen = []

        screen.fill((100,100,100))
        
        for note_sprite in note_sprites:
            xpos = note_sprite.pos[0]
            xwidth = note_sprite.sprite.get_width()

            #Don't bother drawing sprites that are off the screen
            if((xpos+xwidth >= 0) and
               (xpos <= windowWidth)):
                screen.blit(note_sprite.sprite, note_sprite.pos)

                #Play notes that are crossing the line
                if((line_pos_x >= xpos) and
                   (line_pos_x <= xpos + xwidth)):

                    current_hertzen.extend([note_sprite.note.freq])


            #Scroll sprite to the right
            note_sprite.move([-pixels_per_frame, 0])

            #print "{0} {1} {2} {3}".format(xpos, ypos, dx_per_frame, dy_per_frame)

        if(previous_hertzen != current_hertzen):
            with hertzen_lock:
                hertzen = copy.deepcopy(current_hertzen)

        #Line should go over the notes
        pygame.draw.line(screen, [255,255,255], [line_pos_x, 0], [line_pos_x, windowHeight], 5)

        pygame.display.flip() #RENDER WINDOW
        clk.tick(fps) #limit the fps


#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main(sys.argv))
