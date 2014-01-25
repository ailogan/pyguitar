#!/opt/local/bin/python2.7

# show_notes.py
#
# Andrew Logan - 1/24/14
#
# Program written as a test of displaying a sequence of notes in order.

import sys
import math
import pygame
import argparse
import random
import musicxml_parse_test

class SpriteContainer:
    sprite = None
    pos = None

    #Sprite is a pygame.Surface object, pos is a tuple containing the x,y coordinates of where the sprite is on screen.

    def __init__(self, sprite, pos):
        self.sprite = sprite
        self.pos = pos
    
    #Moves the sprite some number of pixels from where it is
    def move(self, velocity):
        self.pos[0] += velocity[0]
        self.pos[1] += velocity[1]

def make_note_sprites_from_notearray(notearray):
    notes = []
    for note_data in notearray:
        when = note_data[0]
        note = note_data[1]
        duration_in_ms = note_data[2]

        key = ""
        
        #format is: [piano_key_#s], duration_in_seconds]
        
        if(note.step is None):
            key = "R"

        else:
            key = note_to_key(note)
            #print key
            
        #Update the previous entry if this note is in a chord
        if(note.is_chord_member):
            chord_notes = notes[-1][0]
            chord_notes.append(key)

        else:
            duration_in_sec = (duration_in_ms / 1000)
            notes.append([[key], duration_in_sec])

    return notes


def positive_int(string):
    num = int(string)
    if (num <= 0):
        raise argparse.ArgumentTypeMessage("need to provide a positive number!")
    
    return num

def main(argv=None):

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
    ms_per_pixel = 10

    pixels_per_ms = 1.0 / ms_per_pixel

    #What color they are
    sprite_color = [200,100,0]

    #Subdivide the window so that each string has its own lane
    #TODO: can eventually get the number of strings from the musicXML file
    num_strings = 6
    sprite_height = (windowHeight / num_strings)

    #Start near the right side of the screen
    x_offset = math.ceil(windowWidth * .9)

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

        sprite_container = SpriteContainer(sprite, [start_x_pos, start_y_pos])

        note_sprites.append(sprite_container)

    clk=pygame.time.Clock()

    # Whooo unit analysis
    # pixel / frame = (pixel / ms) * (ms / frame)

    ms_per_frame = 1000.0 / fps
    pixels_per_frame = pixels_per_ms * ms_per_frame

    while 1:
        for event in pygame.event.get(): #check if we need to exit
                if event.type == pygame.QUIT:pygame.quit();sys.exit()

        screen.fill((100,100,100))

        for note_sprite in note_sprites:
            xpos = note_sprite.pos[0]
            xwidth = note_sprite.sprite.get_width()

            #Don't bother drawing sprites that are off the screen
            if((xpos+xwidth >= 0) and
               (xpos <= windowWidth)):
                screen.blit(note_sprite.sprite, note_sprite.pos)

            #Scroll to the right
            note_sprite.move([-pixels_per_frame, 0])

            #print "{0} {1} {2} {3}".format(xpos, ypos, dx_per_frame, dy_per_frame)

        #Line should go over the notes
        pygame.draw.line(screen, [255,255,255], [windowWidth * .2, 0], [windowWidth * .2, windowHeight], 5)

        pygame.display.flip() #RENDER WINDOW
        clk.tick(fps) #limit the fps


#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main(sys.argv))
