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

    #What color they are
    sprite_color = [200,100,0]

    #Subdivide the window so that each string has its own lane
    #TODO: can eventually get the number of strings from the musicXML file
    num_strings = 6
    sprite_height = (windowHeight / num_strings)

    for note_data in notearray:
        when = note_data[0]
        note = note_data[1]
        duration_in_ms = note_data[2]

        #Is this a rest?
        if(note.step is None):
            continue
        
        sprite_width = math.ceil(float(duration_in_ms) / ms_per_pixel)

        sprite = pygame.Surface([sprite_width, sprite_height])
        sprite.fill(sprite_color)
        
        guitar_string = note.string
        guitar_fret   = note.fret

        words = fontobj.render(str(guitar_fret), True, (200,200,200))

        #Put the fret number onto the note sprite
        sprite.blit(words,[0,0])

        #Now we figure out where this is supposed to be.

        start_x_pos = math.ceil(float(when) / ms_per_pixel)

        #String 6 is on the bottom, string 1 is on the top.  (0,0) is the top left of the screen

        start_y_pos = sprite_height * (guitar_string - 1)

        sprite_container = SpriteContainer(sprite, [start_x_pos, start_y_pos])

        note_sprites.append(sprite_container)

    clk=pygame.time.Clock()

    while 1:
        for event in pygame.event.get(): #check if we need to exit
                if event.type == pygame.QUIT:pygame.quit();sys.exit()

        screen.fill((100,100,100))
        
        image_num = 0

        for note_sprite in note_sprites:
            
            screen.blit(note_sprite.sprite, note_sprite.pos)

            #print "{0} {1} {2} {3}".format(xpos, ypos, dx_per_frame, dy_per_frame)

        pygame.display.flip() #RENDER WINDOW
        clk.tick(fps) #limit the fps


#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main(sys.argv))
