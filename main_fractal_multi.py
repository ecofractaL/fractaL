'''
Multitrack Code - fractaL April 15th 2019

Here, you can find the code to build a multiple MIDI instrument sound using
different environmental variables.

@author: smjacques
'''
import pandas as pd
import fractaL.core as fractal


#import data in a dataframe(df) format
df = pd.read_csv('sample_data/multilong.csv')

test = fractal.normalize_climate_multi(df)

# Let's add some instruments to each track!
instruments_to_add = [
    'music box', 'baritone sax', 'low bongo'
]

multitrack_data_with_instruments = []
for index, track in enumerate(test):
    multitrack_data_with_instruments.append([instruments_to_add[index]] + track)

# While we're at it, let's add a drum track with a solid beat
max_number_of_beats = multitrack_data_with_instruments[0][-1][0]

bass_drum = []
for beat in range(0, int(max_number_of_beats + 1)):
   bass_drum.append((beat, 1)) 

beat_track = ['bass drum 1'] + bass_drum
multitrack_data_with_instruments.append(beat_track)

play_midi_from_data(multitrack_data_with_instruments, track_type='multiple', key='c_sharp_major')