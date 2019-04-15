'''
This is a fractaL code developed to sonify data.
Partially based on Sonify library.

@author: smjacques
'''
import json
import matplotlib.pyplot as plt
import pandas as pd

import fractaL.core as fractal
#from fractaL.core import normalize_climate_data, csv_to_MIDITime_data
from miditime.miditime import MIDITime


with open('sample_data/1880-2019.json') as data_file:    
    climate_json = json.load(data_file)


json_pd = climate_json

normalized_climate_data = fractal.normalize_climate_data(climate_json)
plt.scatter(*zip(*normalized_climate_data))

#print(normalized_climate_data)


'''
Convert Array to pandas
'''
#define labels date and temperature
labels = ['date', 'temperature']
climatefile = pd.DataFrame.from_records(normalized_climate_data, columns=labels)


'''export the dataframe to csv. then read it with csv_to_MIDITime function'''
climatefile.to_csv('sample_data/climatefile.csv', index=False)


climate_ex = fractal.csv_to_MIDITime_data('sample_data/climatefile.csv')

###
#Instantiate the class with a tempo (120bpm), the name file name

#MIDITime(tempo=120, outfile='miditime.mid', seconds_per_year=5, base_octave=5, octave_range=1, custom_epoch=None)
#*For data before 1970 the custom_epoch (UNIX Time) must be setted up 
###


mymidi = MIDITime(120, 'fractal.mid',100, 4, 2)


# Make a beat based on days_sice_epoch(maybe chance to UNIX time - more common used)
my_data_timed = [{'beat': mymidi.beat(d['days_since_epoch']), 'magnitude': d['magnitude']} for d in climate_ex]


#Setting starting time
start_time = my_data_timed[0]['beat']

