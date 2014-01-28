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
    size = None
    pos = None
    note = None

    #Sprite is a pygame.Surface object, pos is a tuple containing the x,y coordinates of where the sprite is on screen.

    def __init__(self, sprite, pos, note):
        self.sprite = sprite
        self.pos = pos
        self.note = note
        self.size = [self.sprite.get_width(), self.sprite.get_height()]
    
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

    chunksize = 128

    osc = data_provider.multi_oscillator(current_hertzen, sample_rate_in_hz=sample_rate, volume = .1, chunksize=chunksize)
        
    while 1:
        previous_hertzen = current_hertzen
        with hertzen_lock:
            current_hertzen = copy.deepcopy(hertzen)

        #Only update the oscillator if the frequencies have changed.
        if(current_hertzen != previous_hertzen):
            osc.update(current_hertzen)

        previous_hertzen = current_hertzen

        data = osc.get_data()
        data_struct = struct.pack('f'*len(data), *data)
        data_buffer = buffer(data_struct)
        audio_stream.write(data_buffer)

def positive_int(string):
    num = int(string)
    if (num < 0):
        raise argparse.ArgumentTypeMessage("need to provide a positive number!")
    
    return num

def main(argv=None):
    global hertzen, hertzen_lock

    #Get commandline arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--wx", help="window width" , default=640, type=positive_int)
    parser.add_argument("--wy", help="window height", default=480, type=positive_int)

    parser.add_argument("--fps", help="frames per second", default=30, type=positive_int)

    parser.add_argument("--infile", help="path to a musicXML file", required=True)

    parser.add_argument("--parts", help="comma-separated list of parts that should be loaded from the musicXML file", default=0)

    parser.add_argument("--scale", help="speed up or slow down the tempo", default=1)

    args = parser.parse_args()

    #Get the dimensions we need
    windowWidth  = args.wx
    windowHeight = args.wy

    fps = args.fps
    
    notearray = []

    print "Loading..."
    music_xml = musicxml_parse_test.mxl_container(args.infile)

    partids = args.parts.split(',')
    
    for part in partids:
        notes = music_xml.get_note_array(int(part))
        print "part {0}: {1}".format(part, len(notes))
        notearray.append(notes)

    notearray.sort(key=lambda x:x[0])

    #Set up pygame
    pygame.init()

    #Set the window title
    pygame.display.set_caption(args.infile)
    
    #Make the special buffer that holds the output that's displayed on the screen
    screen = pygame.display.set_mode([windowWidth,windowHeight])
    
    #Load our sample image
    note_sprites = []

    fontobj = pygame.font.Font(None, 50)

    scale = 1 / float(args.scale)

    #How quickly the sprites will scroll
    ms_per_pixel = 5

    pixels_per_ms = 1.0 / ms_per_pixel

    #Subdivide the window so that each string has its own lane
    #TODO: should eventually get the number of strings from the musicXML file
    num_strings = 6
    num_parts = len(partids)

    lane_height = windowHeight / num_parts
    sprite_height = (lane_height / num_strings)

    #Start near the right side of the screen
    x_offset = math.ceil(windowWidth * .3)
    y_offset = 0

    num_part = 0

    for part in notearray:
        y_offset = num_part * lane_height

        #What color they are
        sprite_color = [(255 / num_parts) * num_part, 100, 0]

        print "loading part {}: size: {} start: {} end: {}".format(num_part, len(part), part[0][0], part[-1][0])

        for note_data in part:
            when = note_data[0]
            note = note_data[1]
            duration_in_ms = note_data[2]

            #Is this a rest?
            if(note.step is None):
                continue

            when *= scale
            duration_in_ms *= scale

            #pixels = ms * (pixels / ms)
            sprite_width = math.ceil(duration_in_ms * pixels_per_ms)

            sprite = pygame.Surface([sprite_width, sprite_height])
            sprite.fill(sprite_color)
        
            #Draw lines on the left and the top of the sprite so we can tell where notes begin
            pygame.draw.lines(sprite, [0,0,0], False, [(0, sprite_height), (0,0), (sprite_width, 0)], 1)
        
            guitar_string = note.string
            guitar_fret   = note.fret

            words = fontobj.render(str(guitar_fret), True, (200,200,200))

            #Put the fret number onto the note sprite
            sprite.blit(words,[0,0])

            #Now we figure out where this is supposed to be.
            #TODO: Don't start scrolling the sprite until it's just about visible on the window.  I imagine this means figuring out how many ms wide the window is.

            start_x_pos = (when * pixels_per_ms) + x_offset

            #String 6 (low E) is on the bottom, string 1 (high E) is on the top.  (0,0) is the top left of the screen

            start_y_pos = sprite_height * (guitar_string - 1) + y_offset

            sprite_container = SpriteContainer(sprite, [start_x_pos, start_y_pos], note)

            note_sprites.append(sprite_container)


        num_part += 1

    clk=pygame.time.Clock()

    # Whooo unit analysis
    # pixel / frame = (pixel / ms) * (ms / frame)

    ms_per_frame = 1000.0 / fps
    pixels_per_frame = pixels_per_ms * ms_per_frame

    #samples / frame = ((samples / second) / 1000) * (ms / frame)

    line_pos_x = windowWidth * .1

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

    #Tracks where we are in the song so that we can avoid moving sprites until we need them.
    cursor_pos = windowWidth
    frames = 1

    while 1:
        for event in pygame.event.get(): #check if we need to exit
                if event.type == pygame.QUIT:pygame.quit();sys.exit()

        previous_hertzen = current_hertzen

        current_hertzen = []

        screen.fill((100,100,100))

        more_notes = False
        
        for note_sprite in note_sprites:
            xpos = note_sprite.pos[0]
            xwidth = note_sprite.size[0]

            if(not more_notes and xpos+xwidth >= 0):
                more_notes = True

            #Don't bother drawing sprites that are off the screen to the left
            if(xpos+xwidth >= 0):
                #Play notes that are crossing the line
                if((line_pos_x >= xpos) and
                   (line_pos_x <= xpos + xwidth)):

                    current_hertzen.extend([note_sprite.note.freq])

                #Don't bother moving or drawing sprites that are off either side of the screen
                if(xpos <= windowWidth):
                    screen.blit(note_sprite.sprite, note_sprite.pos)
                    note_sprite.move([-pixels_per_frame, 0])

                #Jump the sprites that are about to be drawn to the right position.  It's all offscreen anyway so we're wasting moves by incrementing them smoothly.
                else:
                    if(xpos <= cursor_pos):
                        note_sprite.move([-(pixels_per_frame * frames), 0])

        cursor_pos += pixels_per_frame
        frames += 1

            #print "{0} {1} {2} {3}".format(xpos, ypos, dx_per_frame, dy_per_frame)


        #We're done if everything scrolled off of the screen
        if(not more_notes):
            pygame.quit()
            sys.exit()

        if(previous_hertzen != current_hertzen):
            with hertzen_lock:
                hertzen = copy.deepcopy(current_hertzen)

        #Draw lane markers
        for lane in range(0, num_parts):
            pygame.draw.line(screen, [0,0,0], [0, lane_height * lane], [windowWidth, lane_height * lane], 3)
            
            for string in range(0, num_strings):

                lane_x_offset = sprite_height * .5 + (sprite_height * string) + (lane_height * lane)
                pygame.draw.line(screen, [255,255,255], [0, lane_x_offset], [windowWidth, lane_x_offset], 1)

        #Line for where the notes are played should go over the notes
        pygame.draw.line(screen, [255,255,255], [line_pos_x, 0], [line_pos_x, windowHeight], 3)

        pygame.display.flip() #RENDER WINDOW
        clk.tick(fps) #limit the fps


#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main(sys.argv))
