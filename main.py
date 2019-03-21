"""
This is a fractaL code developed to sonify data.
Partially based on Sonify library.

@author: saulo jacques
"""
import csv
#import io
import json
#import random
#import sonify
#import numpy as np
#import pygame
#import scipy.signal
#import astropy.io.fits
import matplotlib.pyplot as plt
#import sys
import pandas as pd

from miditime.miditime import MIDITime
#from IPython.display import Audio
#from time import sleep
#from pretty_midi import note_name_to_number
#from midiutil.MidiFile import MIDIFile


def get_closest_midi_value(value, possible_values):
    return sorted(possible_values, key=lambda i: abs(i - value))[0]


def scale_y_to_midi_range(data, new_min=0, new_max=127):
    """
    midi notes have a range of 0 - 127. Make sure the data is in that range
    data: list of tuples of x, y coordinates for pitch and timing
    min: min data value, defaults to 0
    max: max data value, defaults to 127
    return: data, but y normalized to the range specified by min and max
    """
    if new_min < 0 or new_max > 127:
        raise ValueError('Midi notes must be in a range from 0 - 127')

    x, y = zip(*data)
    new_y = scale_list_to_range(y, new_min, new_max)

    return list(zip(x, new_y))


def scale_list_to_range(list_to_scale, new_min, new_max):
    old_min = min(list_to_scale)
    old_max = max(list_to_scale)
    return [get_scaled_value(value, old_min, old_max, new_min, new_max) for value in list_to_scale]


def get_scaled_value(old_value, old_min, old_max, new_min, new_max):
    return ((old_value - old_min)/(old_max - old_min)) * (new_max - new_min) + new_min



def normalize_climate_data(climate_json):
    years = [int(year) for year in climate_json['data'].keys()]
    temp_anomolies = [float(temp_anomaly) for temp_anomaly in climate_json['data'].values()]

    normalized_years = scale_list_to_range(years, new_min=0, new_max=30)
    normalized_temp_anomolies = scale_list_to_range(temp_anomolies, new_min=30, new_max=127)


    normed_climate_data = list(zip(normalized_years, normalized_temp_anomolies))
    
    return normed_climate_data


with open('sample_data/1880-2019.json') as data_file:    
    climate_json = json.load(data_file)


json_pd = climate_json

normalized_climate_data = normalize_climate_data(climate_json)
plt.scatter(*zip(*normalized_climate_data))


'''
Convert Array to pandas
'''
#define labels date and temperature
labels = ['date', 'temperature']
climatefile = pd.DataFrame.from_records(normalized_climate_data, columns=labels)


'''
Using MIDItime
'''

def csv_to_MIDITime_data(filename):
    mydata = []
    with open(filename, 'r') as f:
        reader=csv.reader(f)
        next(reader, None) #this is added only in case of a file with header
        for row in reader:
            mydict = {'days_since_epoch': float(row[0]) , 'magnitude': float(row[1])}
            mydata.append(mydict)
    return mydata

'''export the dataframe to csv. then read it with csv_to_MIDITime function'''
climatefile.to_csv('sample_data/climatefile.csv', index=False)


climate_ex = csv_to_MIDITime_data('sample_data/climatefile.csv')


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


def mag_to_pitch_tuned(magnitude):
    # Where does this data point sit in the domain of your data? (I.E. the min magnitude is 3, the max in 5.6). In this case the optional 'True' means the scale is reversed, so the highest value will return the lowest percentage.
    scale_pct = mymidi.linear_scale_pct(10, 130, magnitude)

    # Another option: Linear scale, reverse order
    #scale_pct = mymidi.linear_scale_pct(3, 5.7, magnitude, True)

    # Another option: Logarithmic scale, reverse order
    # scale_pct = mymidi.log_scale_pct(3, 5.7, magnitude, True)

    # Pick a range of notes. This allows you to play in a key.
    c_major = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

    #Find the note that matches your data point
    note = mymidi.scale_to_note(scale_pct, c_major)

    #Translate that note to a MIDI pitch
    midi_pitch = mymidi.note_to_midi_pitch(note)

    return midi_pitch

def mag_to_attack(magnitude):
    # Where does this data point sit in the domain of your data? (I.E. the min magnitude is 3, the max in 5.6). In this case the optional 'True' means the scale is reversed, so the highest value will return the lowest percentage.
    scale_pct = mymidi.linear_scale_pct(30, 127, magnitude)
    
    max_attack = 10

    adj_attack = (1-scale_pct)*max_attack + 70
    #adj_attack = 100

    return adj_attack


note_list = []

for d in my_data_timed:
    note_list.append([
        d['beat'] - start_time,
        mag_to_pitch_tuned(d['magnitude']),
        100,
        #mag_to_attack(d['magnitude']),  # attack
        0.5  # duration, in beats
    ])
    


# Add a track with those notes
mymidi.add_track(note_list)

# Output the .mid file
mymidi.save_midi()