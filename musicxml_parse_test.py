#!/usr/bin/python

# musicxml_parse_test
#
# Andrew Logan - 1/14/14
#
# The music21 library is awesome but has two major drawbacks: digging
# through a series of Streams to find Measures that contain Notes and
# Chords is a PITA, and it throws out the tableture information that I
# need.  So maybe the right thing to do is to just parse the raw XML
# and build the data structures I need instead.

import sys

import argparse

import xml.etree.ElementTree as ET

#even simpler container for a rest
class rest:
    duration = None

    def __init__(self, duration = None):
        self.duration = duration

#Very simple container for a note  If there's no step and no octave then it's a rest.
class note:
    step = None     #Which note (A, B, C, whatever)
    octave = None   #which octave
    duration_in_ticks = None #how many ticks
    is_chord_member = None #Is it part of a chord?

    def __init__(self, step = None, octave = None, duration_in_ticks = None, is_chord_member = None):
        self.step = step
        self.octave = octave
        self.duration_in_ticks = duration_in_ticks
        self.is_chord_member = is_chord_member

class mxl_container:
    #The current state of a couple of important pieces of metadata
    tempo = None
    beats = None
    beat_type = None

    #divisions are the number of ticks in a quarter note
    divisions = None

    #Seems like it'll be useful
    ms_per_tick = None
    current_ms = None

    root = None
    parts = None

    #Path to a musicxml file
    def __init__(self, xmlfile):
        self.tempo = 90 #The default according to the musicxml docs.
        self.current_ms = 0

        tree = ET.parse(xmlfile)
        self.root = tree.getroot()

        self.parts = []

        #Try to stuff the XML file into a useful container.

        #parts have measures
        for part in self.root.findall('part'):
            measures = []

            #measures have all sorts of junk
            for measure in part.findall('measure'):
                measures.append(measure)

            self.parts.append(measures)

    def update_ms_per_tick(self):
        if(self.tempo == None):
            return

        if(self.divisions == None):
            return

        #MusicXML tempo is in quarter-notes / minute
        
        ticks_per_minute = self.tempo * self.divisions

        self.ms_per_tick = 1 / (float(ticks_per_minute) / 60 / 1000)

    def parse_note(self, note_node):
        step = None
        octave = None
        duration_in_ticks = None
        is_chord_member = None

        #Is there a pitch?
        if (note_node.find("./pitch") is not None):
            step = note_node.find("./pitch/step").text
            octave = note_node.find("./pitch/octave").text

        #Sounded notes and rests both have durations
        duration_in_ticks = note_node.find("./duration").text

        if (note_node.find("./chord") is not None):
            is_chord_member = True

        else:
            is_chord_member = False

        return note(step=step, octave=octave, duration_in_ticks=duration_in_ticks, is_chord_member=is_chord_member)

    def parse_time(self, item):
        for element in item:
            #numerator of the time signature (how many of the fundamental notes are in a measure)
            if(element.tag == "beats"):
                self.beats = int(element.text)

            #denominator of the time signature (which type of note is the fundamental note)
            elif(element.tag == "beat-type"):
                self.beat_type = int(element.text)

    def parse_direction(self, item):
        for element in item:
            if(element.tag == "sound"):
                self.tempo = int(element.attrib['tempo'])

    def parse_attributes(self, item):
        for element in item:

            #The number of ticks in a quarter note, according to the musicXML documentation.
            if(element.tag == "divisions"):
                self.divisions = int(element.text)

            elif(element.tag == "time"):
                self.parse_time(element)

    def parse_measure(self, item):
        if(item == None):
            return

        notearray = []

        for element in item:
            #Yaaaaaaaay XML
            if(element.tag == "attributes"):
                self.parse_attributes(element)

                #Need to do this when we update the tempo or the divisions
                self.update_ms_per_tick()

            elif(element.tag == "direction"):
                self.parse_direction(element)

                #Need to do this when we update the tempo or the divisions
                self.update_ms_per_tick()

            elif(element.tag == "note"):
                note = self.parse_note(element)
                when = None
                duration_in_ms = int(note.duration_in_ticks) * self.ms_per_tick
                
                #Is this part of a chord? (confusingly enough this flag doesn't seem to be set for the root note)
                if(note.is_chord_member):

                    #Use the previous timing
                    when = notearray[-1][0]

                else:
                    when = self.current_ms

                    #And increment the time
                    self.current_ms += duration_in_ms

                notearray.append([when, note, duration_in_ms])

        return notearray

    #Get the notes
    def get_note_array(self):

        notearray = []

        #For now we're only looking at the first part
        measures = self.parts[0]

        for measure in measures:
            notes = self.parse_measure(measure)
            notearray.extend(notes)

        return notearray

#TODO: Doesn't handle tempo shifts yet.
def get_tempo(xmlroot):
    sound = xmlroot.findall(".//sound")

    #Have I mentioned how much I don't like XML?
    tempo = int(sound[0].attrib['tempo'])

    print tempo

    return tempo

#TODO: The standard allows this to change at will
def get_quarter_note_divisions(xmlroot):
    divisions = xmlroot.findall("./attributes/divisions")
    
    return int(divisions[0].text)


def walk_tree(element, spaces):
#    if(not element):
#        print "bail: " + str(element)
#        return

    indent = ""

    for x in range(0, spaces):
        indent += " "
        
    text = ""

    if(element.text != None and
       ord(element.text[0]) != 0xA):
        text = element.text

    print "{0}{1}: {2} {3}".format(indent, element.tag, element.attrib, text)

    for child in element:
        walk_tree(child, spaces+1)

def play_file(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    walk_tree(root, 0)
    
    #for element in tree.iter():
    #    print "{0}: {1} {2}".format(element.tag, element.attrib, element.text)

def walk_parts(thing, level):
    indent = ""
    
    for x in range(0, level):
        indent += " "

    for item in thing:
        if( isinstance(item, list) ):
            walk_parts(item, level+1)
        
        elif (isinstance(item, ET.Element)):
            if(item.tag == "measure"):
                walk_tree(item, level+1)

            else:
                print "found element"

        else:
            print "{0}{1}".format(indent, item)

def main(argv=None):

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--infile", help="path to a wav file", required=True)

    args = parser.parse_args()
    
    #play_file(args.infile)

    music_xml = mxl_container(args.infile)

    notearrays = music_xml.get_note_array()

    for notearray in notearrays:
        when = notearray[0]
        note = notearray[1]
        duration_in_ms = notearray[2]

        what = ""
        note_name = ""

        #What is the name of this note?
        if(note.step is not None and
           note.octave is not None):
            note_name = " {0}{1}".format(note.step, note.octave)

            #Root notes, weirdly enough, don't get the chord flag
            if(note.is_chord_member):
                what = "chord"

            else:
                what = "note"

        #It's a rest if it doesn't have a name
        else:
            what = "rest"

        print "Found {0:5s}{1:3s}: {2:9.2f} ms at {3:9.2f} ms".format(what, note_name, duration_in_ms, when)

    
    print "tempo: {0}, divisions: {1}, ms_per_tick: {2}".format(music_xml.tempo, music_xml.divisions, music_xml.ms_per_tick)

    #walk_parts(music_xml.parts, 0)

#Give main() a single exit point (see: http://www.artima.com/weblogs/viewpost.jsp?thread=4829)
if __name__ == "__main__":
    sys.exit(main())
