#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Using specific functions for sonification. This code is partially inspired by
the project Sonify (https://github.com/erinspace/sonify) with some
modifications to be applied on environmental data.
Although some parameters were changed, we decided to keep some functions name
as originally defined by Erin Braswell at her work.
Currently our focus will be the temperature, conductivity and salinity data.
Further steps: biodiversity, birds and big mammals migratory data.

version 0.0.1
March, 3rd 2019
sjacques 
"""
#Playing MIDI

#Firstly we define some functions to make it possible in a easy way

import csv
import io
import numpy as np
import pygame

from midiutil.MidiFile import MIDIFile
from pretty_midi import note_name_to_number
from time import sleep
from .midisource import KEYS, INSTRUMENTS, PERCUSSION

'''
Defining the starting note based on the subtraction of y_values by notes_in_key
new_y.append create values based on the ??? of y and traspose_value
'''
def make_first_number_match_key(y_values, notes_in_key):
    first_note_in_key = notes_in_key[0]
    transpose_value = first_note_in_key - y_values[0]
    new_y = []
    for y in y_values:
        new_y.append(y + transpose_value)

    return new_y

'''
    Convert a key name to notes, using C3=60
    :param key: String matching one of the values in pre-defined KEY dict
    :param octave_start: octave for the first note, as defined by C3=60
    :param number_of_octaves: The number of octaves to include in the list
'''
def key_name_to_notes(key, octave_start=1, number_of_octaves=4):
    key = KEYS.get(key)
    if not key:
        raise ValueError('No key by that name found')

    notes = []
    octave = octave_start + 1
    while len(notes) < number_of_octaves * 7:
        for note in key:
            note_with_octave = note + str(octave)
            note_number = note_name_to_number(note_with_octave)
            if note_number % 12 == 0 and len(notes) != 0:
                octave += 1
                note_with_octave = note + str(octave)
                note_number = note_name_to_number(note_with_octave)
            notes.append(note_number)

    return notes

'''
Define notes using the more close/possible value of MIDI.
Itis done sorting the "possible values" according to lambda i: abs(i - value)
'''

def get_closest_midi_value(value, possible_values):
    return sorted(possible_values, key=lambda i: abs(i - value))[0]


'''
 midi notes have a range of 0 - 127. Make sure the data is in that range
    data: list of tuples of x, y coordinates for pitch and timing
    min: min data value, defaults to 0
    max: max data value, defaults to 127
    return: data, but y normalized to the range specified by min and max
'''
def scale_y_to_midi_range(data, new_min=0, new_max=127):
    if new_min < 0 or new_max > 127:
        raise ValueError('Midi notes must be in a range from 0 - 127')

    x, y = zip(*data)
    new_y = scale_list_to_range(y, new_min, new_max)

    return list(zip(x, new_y))


'''
Use the min and max values from "old_value" and the new parameters to set scaled
values inside the range
'''
def get_scaled_value(old_value, old_min, old_max, new_min, new_max):
    return ((old_value - old_min)/(old_max - old_min)) * (new_max - new_min) + new_min


'''
set a list inside a MIDI range defined by new_min and new_max
the output is based on the list_to_scale and uses get_scaled_value function
'''
def scale_list_to_range(list_to_scale, new_min, new_max):
    old_min = min(list_to_scale)
    old_max = max(list_to_scale)
    return [get_scaled_value(value, old_min, old_max, new_min, new_max) for value in list_to_scale]


'''
Restrict the x range to something that's a multiple of the number of steps given!
'''
def quantize_x_value(list_to_quantize, steps=0.5):
    quantized_x = []
    for x in list_to_quantize:
        quantized_x.append(round(steps * round(float(x) / steps), 2))
    return quantized_x

'''
Access the .xxxxx file and set up the instrument sound
'''
def get_instrument(instrument_name):
    instrument_type = 'melodic'
    program_number = INSTRUMENTS.get(instrument_name.lower())
    if not program_number:
        program_number = PERCUSSION.get(instrument_name.lower())
        instrument_type = 'percussion'
        if not program_number:
            raise AttributeError('No instrument or percussion could be found by that name')
    return program_number - 1, instrument_type


'''
Define the key. As defined before, the percussion is a default. Otherwise it will be
necessary to use key_name_to_notes, make_first_number_match_key and scale_list
to_range to fit the range for other instruments.
    line 140: Finding the index of the note closest to all the notes in the options list
'''
def convert_to_key(data, key, number_of_octaves=4):
    instrument, instrument_type = None, None
    if type(data[0]) != tuple:
        instrument = data.pop(0)
        _, instrument_type = get_instrument(instrument)

    x, y = zip(*data)

    if instrument_type == 'percussion':
        new_y = y
    else:
        notes_in_key = key_name_to_notes(key, number_of_octaves=number_of_octaves)

        transposed_y = make_first_number_match_key(y, notes_in_key)
        scaled_y = scale_list_to_range(transposed_y, new_min=min(notes_in_key), new_max=max(notes_in_key))

        new_y = []
        for note in scaled_y:
            new_y.append(get_closest_midi_value(note, notes_in_key))

    processed_data = list(zip(x, new_y))

    if instrument:
        processed_data = [instrument] + processed_data

    return processed_data


'''
This function is applied to JSON data (in this case for climate data)

'''
def normalize_climate_data(climate_json):
    years = [int(year) for year in climate_json['data'].keys()]
    temp_anomolies = [float(temp_anomaly) for temp_anomaly in climate_json['data'].values()]

    normalized_years = scale_list_to_range(years, new_min=0, new_max=30)
    normalized_temp_anomolies = scale_list_to_range(temp_anomolies, new_min=30, new_max=127)


    normed_climate_data = list(zip(normalized_years, normalized_temp_anomolies))
    
    return normed_climate_data


'''
Import df to list and cetify we don't have NaN
With this code we generate a file for multitrack analisys ike that created by
multitrack_data on sonify: a nested list of tuples
'''

def normalize_climate_multi(df):
    df = df.replace(np.nan, 0)

#From df to list: year is the key and the othe variables will be its values
    years_list = [int(year) for year in df['Date'].keys()]
    temperature_list = [float(temp) for temp in df['Temperature'].tolist()]
    conductivity_list = [float(conduct) for conduct in df['Condutivity'].tolist()]
    salinity_list = [float(sal) for sal in df['Salinity'].tolist()]
    
#normalize data
    normalized_years_multi = scale_list_to_range(years_list, new_min=0, new_max=30)
    normalized_temp_multi = scale_list_to_range(temperature_list, new_min=30, new_max=127)
    normalized_cond_multi = scale_list_to_range(conductivity_list, new_min=30, new_max=127)
    normalized_sal_multi = scale_list_to_range(salinity_list, new_min=30, new_max=127)
    
    normed_climate_multi = list(zip( normalized_years_multi, normalized_temp_multi))
    normed_cond_multi = list(zip( normalized_years_multi, normalized_cond_multi))
    normed_sal_multi = list(zip( normalized_years_multi, normalized_sal_multi))
    
    normed_multi = [normed_climate_multi]+[normed_cond_multi]+[normed_sal_multi]
    
    return(normed_multi)


'''
To use JSON with MIDItime library. It converts the df to a dictionary

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


"""
Export the MIDIfile
data: dictionary of x, y coordinates for pitch and timing
Optional: add a string to the start of the data list to specify instrument!
type: the type of data passed to create tracks. Either 'single' or 'multiple'
"""

def write_to_midifile(data, track_type='single'):

    if track_type not in ['single', 'multiple']:
        raise ValueError('Track type must be single or multiple')

    if track_type == 'single':
        data = [data]

    memfile = io.BytesIO()
    midifile = MIDIFile(numTracks=len(data), adjust_origin=False)

    track = 0
    time = 0
    program = 0
    channel = 0
    duration = 1
    volume = 90

    for data_list in data:
        midifile.addTrackName(track, time, 'Track {}'.format(track))
        midifile.addTempo(track, time, 120)

        instrument_type = 'melodic'
        if type(data_list[0]) != tuple:
            program, instrument_type = get_instrument(data_list.pop(0))

        if instrument_type == 'percussion':
            volume = 100
            channel = 9

        # Write the notes we want to appear in the file
        for point in data_list:
            time = point[0]
            pitch = int(point[1]) if instrument_type == 'melodic' else program
            midifile.addNote(track, channel, pitch, time, duration, volume)
            midifile.addProgramChange(track, channel, time, program)

        track += 1
        channel = 0

    midifile.writeFile(memfile)

    return memfile


'''
To play MIDI without having to save to a file
This is is using pygame as we can see.
'''
def play_memfile_as_midi(memfile):
    pygame.init()
    pygame.mixer.init()
    memfile.seek(0)
    pygame.mixer.music.load(memfile)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        sleep(1)
    print('Done playing!')


"""
As input_data it is used a list of tuples, or a list of lists of tuples to add
as separate tracks

eg:
    input_data = [(1, 7), (7, 9)]
        OR
    input_data = [
        [(1, 3), (5, 2)],
        [(4, 1), (3, 12)]
    ]

key: key to play back the graph -- see constants.py for current choices
number_of_octaves: number of octaves used to restrict the music playback
when converting to a key
optional -- append an instrument name to the start of each data list to play
back using that program number!
"""
def play_midi_from_data(input_data, key=None, number_of_octaves=4, track_type='single'):

    if key:
        if track_type == 'multiple':
            data = []
            for data_list in input_data:
                data.append(convert_to_key(data_list, key, number_of_octaves))
        else:
            data = convert_to_key(input_data, key, number_of_octaves)
    else:
        data = input_data

    memfile = write_to_midifile(data, track_type)
    play_memfile_as_midi(memfile)