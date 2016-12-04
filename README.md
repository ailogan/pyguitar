# pyguitar

A python-based synthesizer that reads MusicXML files and does a bunch of math to make sound.

## Installation

Requires pygame

## Usage

There are a couple of different programs embedded in this project.

### pyguitar.py

Run the FFT algorithm on a recording to figure out which note is being played.  Example:

```bash
./pyguitar.py --infile Guitar_Standard_Tuning.wav 
```

### show_notes.py

Pops up a pygame window and scrolls guitar tablature notation past in different lanes for each part.

```bash
./show_notes.py --infile g_major.xml --parts 0

./show_notes.py --infile led_zeppelin_stairway_to_heaven_solo.xml --parts 0,1,2,3,4,5,6,7
```
