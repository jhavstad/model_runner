#! /usr/bin/env python


# NOTE: May 21, 2014 - Version 0.1 Beta
# NOTE: May 21, 2014 - Version 0.11 Beta - Fixed error where directory was not prepended to filename
# NOTE: May 21, 2014 - Version 0.12 Beta - Added print outputs to indicate which files have been generated
# NOTE: May 21, 2014 - Version 0.13 Beta - Removed prepended directory name if it is included
# NOTE: May 21, 2014 - Version 0.14 Beta - Fixed directory listing on Windows, e.g. change '\' to '/' and replaced characters that may be confused as escape characters
# NOTE: May 21, 2014 - Version 0.15 Beta - Made second paramter, delimiter, to method run_jobs a default parameter
# NOTE: May 21, 2014 - Version 0.15a Beta - Added other common escape characters to look out for and added tabs to header output

# NOTE: May 22, 2014 - Version 0.16 Beta - Added functionality to produce single files for a station for temperature and precipitation
# NOTE: May 22, 2014 - Version 0.16 Beta - Added creation of output directory to send output files to
# NOTE: May 22, 2014 - Remember the following: tr -d '\015' < batch_job_win.py > batch_job_unix.py - to replace CRLF EOL markers (win style) with LF EOLF markers (unix style)
# NOTE: May 22, 2014 - Version 0.16a Beta - Changed method of verifying 'output' directory

# NOTE: May 22, 2014 - Version 0.17 Beta - Added GUI elements - changed input parameters so that an output path may specified (or use default)

# NOTE: May 27, 2014 - Version 0.18 Beta - Fixed issues related to outputting years in sequence and outputting files for different output
# NOTE: May 27, 2014 - Version 0.18a Beta - Changed output to create only temperature and precipitation files for a station instead of multiple files per model (unless specified)

# NOTE: May 27, 2014 - Version 0.19 Beta - Added functionality to select output by beginning and ending years - added functionality to GUI
# NOTE: May 27, 2014 - Version 0.19a Beta - Minor bug fixes
# NOTE: May 27 & 28, 2014 - Version 0.19b Beta - Minor bug fixes

# NOTE: May 28, 2014 - Version 0.20 Beta - Changed GUI grid layout - changed program arguments to accept parameters for multiple runs - Using ttk GUI toolkit
# NOTE: May 29, 2014 - Version 0.20a Beta - Fixed focus bugs - added threading component so that processing of files runs in parallel to the GUI
# NOTE: May 29, 2014 - Version 0.20b Beta - Fixed bug that mistakenly placed wdigets into custom object instead of the main frame attribute

# NOTE: Jun 2, 2014 - Version 0.21 Beta - Added additional job parameters, along with GUI, to capture user requirements to process 10 year, 20 year, and custom range of averages

# NOTE: Jun 13, 2014 - Version 0.22 Beta - Changed output columns to include the runs and eras also

# NOTE: Jun 24, 2014 - Version 0.23 Beta - Changed year output values to indicate that only an inclusive year range is used to calculate averages

# NOTE: Jun 25, 2014 - Version 0.24 Beta - Added log file to receive output for debug information
# NOTE: Jun 26, 2014 - Version 0.24a Beta - Added additional log file information

# NOTE: Jun 26, 2014 - Version 0.25 Beta - Added message dialog to indicate that job has completed and asks the user if the job list should be cleared

# NOTE: Jun 26, 2014 - Version 0.26 Beta - Added line graphs and pandas data frames
# NOTE: Jun 27, 2014 - Version 0.27 Beta - Added Graphing GUI

# NOTE: Jun 28, 2014 - Version 0.27a Beta - Additions to plots and plot GUI

# NOTE: Jun 30, 2014 - Version 0.27b Beta - Additions to plots and plot GUI.  Modified main GUI to pop-up Plot GUI afterwards.

# NOTE: Jul 1, 2014 - Version 0.27c Beta - Added mulithreading to plot creation task. Fixed bug on Windows associated with trying to create GUI components from outside the main thred

# NOTE: Jul 2, 2014 - Version 0.27d Beta - Fixed bugs associated with graphs and related plotting data


# NOTE: Jul 28, 2014 - Version 0.28 Beta - Changing ttk based widgets to PMW based widgets

# NOTE: Aug 21, 2014 - Version 0.29 Beta - Adding DnD panel for choosing plots along with 'OK' and 'Cancel' buttons to confirm or close said DnD panel

# NOTE: Sep 10, 2014 - Version 0.29 Beta - Added install script to program

# NOTE: Sep 11, 2014 - Version 0.30 Beta - Fixed plot elements - Fixed bugs that cause errors when the plots are closed

# NOTE: Sep 12, 2014 - Version 0.31 Beta - Fixed stack ordering of windows so that last window opened prior to opening to another shows up when the other closes - Fixed multiple bugs when new program jobs are created, removed, cancelled, etc. - Added log filename to bottom of plot window - Changed plot window to display not plots initially - Changed Plot Window so that it can be resized by the user

# NOTE: Sep 23, 2014 - Version 0.32 Beta - Added MyPmwBase.py and MyPmwScrolledFrame.py to local project so that the module Pmw does not need to be installed on other hosts

# NOTE: Oct 1, 2014 - Version 0.33 Beta - Removed limitations to lengths of Station, Model, and Run names - Will also remove '-' and '_', in addition to ' ', from the Station Name so that 'Station X', 'Station-X', and 'Station_X' are all the same

# NOTE: Dec 18, 2014 - Version 0.34 Beta - Fixed bug that took the year difference as an included value in the temp vs. precip scatter plot, skewing the resulting graph

__VERSION__ = '0.34 Beta'

# Matplotlib, and by extension ggplot, automatically generate GUIs which conflict with the GUI implementation
# defined here.  So, we need to "suppress" this inclination via the following statements.
import matplotlib as mpl
mpl.use('Agg')

import os
import sys
import string
from optparse import OptionParser
import logging
import datetime
import time

import Tkinter
import ttk
import ModelRunnerGUI

# NOTE: There is an error message that crops up when importing ggplot that refrences pandas.
# NOTE: Anything that is imported that itself import ggplot also causes the error message to crop up
#import ggplot
import ModelRunnerPlots

'''
written by Jonathan Havstad in 2014
email: jjhavstad@gmail.com
twitter: @jjhavstad
'''

# NOTE: The following are the keywords that are added to the job params (i.e. job args, input args, etc.)
# 'job_id'
# 'delimiter'
# 'individual_files'
# 'output_directory'
# 'start'
# 'end'
# 'log'
# 'start_time'
# The following are additional parameters added by the GUI
# 'calculate_one_directory'
# 'calculate_two_directory'
# 'calculate_custom_range'
# 'custom_range'
# Additional elements
# 'line_number'
# 'list_text'
# 'log_filename'

def get_time_diff_secs(startdate, enddate):
    # Fortunately, we have a timedelta function in datetime that can compute differences between data objects
    epoch_starttime_secs = time.mktime(startdate.timetuple())
    epoch_endtime_secs = time.mktime(enddate.timetuple())
    return (epoch_endtime_secs - epoch_starttime_secs)

def calculate_avgs_for_model(input_filename, station, col_name):
    '''
    This calculates the averages for a given time period.
    @arg input_filename The filename of the file to process
    @arg temp_table the temperature table to add the elements to
    @arg precip_table the precipitation table to add the elements to
    @arg col_name the name of the column to add
    Returns a 3-tuple containing the years, the temperature, and the precipitation
    '''

    input_file = None
    if input_filename != None:
        input_file = open(input_filename, "r")

    if input_file != None and not input_file.closed:

        # Check to make sure this is true model file
        headers = input_file.readline().strip().split(' ')
        if len(headers) != 6 or headers[0] != 'Year' or headers[1] != 'Month' or headers[2] != 'Day' or \
            headers[3] != 'Tmax_F' or (headers[4] != 'qqTmin_F' and headers[4] != 'Tmin_F') or headers[5] != 'Prcp_in_100':
            return False

        prev_year = None

        temp_avg = 0
        precip_sum = 0
        cnt = 0

        if 'first_value' not in station:
            station['first_value'] = None

        if 'end_value' not in station:
            station['end_value'] = None

        if 'header' not in station['temp_table']:
            station['temp_table']['header'] = list()
        if 'year' not in station['temp_table']['header']:
            station['temp_table']['header'].append('year')
        if col_name not in station['temp_table']['header']:
            station['temp_table']['header'].append(col_name)
        if 'data' not in station['temp_table']:
            station['temp_table']['data'] = dict()

        if 'header' not in station['precip_table']:
            station['precip_table']['header'] = list()
        if 'year' not in station['precip_table']['header']:
            station['precip_table']['header'].append('year')
        if col_name not in station['precip_table']['header']:
            station['precip_table']['header'].append(col_name)
        if 'data' not in station['precip_table']:
            station['precip_table']['data'] = dict()

        for line in input_file:
            # Replace 3 and 2 character wide whitespace with single wide
            line = line.strip()
            data = line.split(' ')
            while '' in data:
                data.remove('')
            #print data
            year, month, day, tmax, tmin, precip = data
            year = int(year)
            month = int(month)
            tmax = float(tmax)
            tmin = float(tmin)
            precip = float(precip)

            if station['first_value'] == None or year < station['first_value']:
                station['first_value'] = year

            if station['end_value'] == None or year > station['end_value']:
                station['end_value'] = year

            if prev_year != None and prev_year != year:
                    temp_avg /= cnt

                    # Add values to propert tables
                    if prev_year not in station['temp_table']['data']:
                        station['temp_table']['data'][prev_year] = dict()
                    station['temp_table']['data'][prev_year][col_name] = temp_avg

                    if prev_year not in station['precip_table']['data']:
                        station['precip_table']['data'][prev_year] = dict()
                    station['precip_table']['data'][prev_year][col_name] = precip_sum

                    temp_avg = 0
                    precip_sum = 0
                    cnt = 0

            prev_year = year
            temp_avg += float(tmax + tmin) / 2.0
            precip_sum += float(precip)
            cnt += 1

        # Add last values to table
        if prev_year != None:
            temp_avg /= cnt

            if prev_year not in station['temp_table']['data']:
                station['temp_table']['data'][prev_year] = dict()
            station['temp_table']['data'][prev_year][col_name] = temp_avg

            if prev_year not in station['precip_table']['data']:
                station['precip_table']['data'][prev_year] = dict()
            station['precip_table']['data'][prev_year][col_name] = precip_sum

    # Finally, close out the file
    if input_file != None:
        input_file.close()

    return True

def build_file_list(directory):
    try:
        directory_listing = os.listdir(directory)
    except OSError as oserror:
        print(directory + ': ' + repr(oserror[1]))
        return None

    input_files = list()
    # Try to eliminate files by excluding those without a *.txt extension
    for f in directory_listing:
        if f.find(".txt") != -1:
            input_files.append(directory + '/' + f)

    return input_files

def get_default_output_directory(input_directory):
    output_directory = input_directory + '/output/'
    return create_output_directory(output_directory)

def create_output_directory(output_directory):
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)
    return output_directory

def create_station_name(station):
    station_name = station.translate(string.maketrans("",""), ' ')
    station_name = station_name.translate(string.maketrans("",""), '_')
    station_name = station_name.translate(string.maketrans("",""), '-')
    print 'Station name: ' + str(station_name)
    #station_name = station_name[0:7]

    return station_name

def create_model_name(model):
    model_name = model
    #model_name = model[0:7]
    return model_name

def create_model_run_name(model_run):
    #model_run_name = model_run[0:5]
    model_run_name = model_run
    return model_run_name

def create_column_name(params):
    try:
        col_name = create_model_name(params['Model']) + '_' + params['Era'] + '_' + create_model_run_name(params['Run'])
    except KeyError as ke:
        return None
    return col_name

def get_value(data_table, cur, last, col, log):
    value_sum = 0.0
    if cur > last:
        return 0.0
    n = float(last - cur)
    n_actual = n
    for year in range(cur, last):
        if year in data_table and col in data_table[year]:
            value_sum += float(data_table[year][col])
        else:
            # NOTE: Jun 26, 2014 - Should missing values be replaced with imputation?
            # If so, then the value n should be an actual count of the present values, correct?
            n_actual -= 1
            if log:
                logging.warn(col + ' is missing the year ' + str(year) + '.  The computed averages are estimations (assuming the missing value is an imputed value).')
    computed_average = value_sum / n_actual
    average = computed_average
    return average

# NOTE: Jun 26, 2014 - This function has logging enabled
def write_table(table, first, last, out_file, col_names, log, year_range=1):
    # Make sure the base dictionaries are available
    if 'header' not in table or 'data' not in table:
        return False

    # Write out the header
    #out_file.write(str(col_names) + '\n')
    index = 0
    for header_item in col_names:
        out_file.write(header_item)
        if index < (len(col_names) - 1):
            out_file.write('\t')
        index += 1
    out_file.write('\n')
    out_file.flush()

    # Write out the data

    cur = first
    while cur <= (last - year_range + 1):
        try:
            # Double precaution with try-catch statement as well as conditional
            if cur in table['data']:

                index = 0
                for col in col_names:
                    if col == 'year':
                        if year_range > 1:
                            out_file.write(str(cur) + '-' + str(cur+year_range-1))
                        else:
                            out_file.write(str(cur))
                    elif col in table['data'][cur]:
                        data = get_value(table['data'], cur, cur + year_range, col, log)
                        out_file.write(str(data))
                    #else:
                        #if log:
                            #logging.warn(col + ' missing date for year range for ' + str(cur+year_range-1))
                    if index < (len(col_names) - 1):
                        out_file.write('\t')
                    index += 1

            out_file.write('\n')
            cur += 1
            if (cur - first) % 100 == 0:
                out_file.flush()

        except KeyError as ke:
            print('KeyError: ' + str(ke))
            continue

    # Clean up by flushing any remaining elements in the file buffer to file and then closing the file
    out_file.flush()
    out_file.close()

    return True

# NOTE: Jun 26, 2014 - This function has logging enabled
def write_file(filename, data_table, start, end, model, log, year_range=1):
    file_write_success = False
    f = open(filename, 'w')
    if log:
        logging.info('Attempting to write file: ' + filename)
    if not f.closed:
        if write_table(data_table, start, end, f, model, log, year_range):
            if not log:
                print('Finished: ' + filename)
            file_write_success = True
        else:
            if not log:
                print('Failed: ' + filename)
            file_write_success = False
    else:
        if log:
            logging.warn('File is not open!')

    # Output logging information
    if log:
        if file_write_success:
            logging.info('Successfully wrote file: ' + filename)
        else:
            logging.warn('Failed to write file: ' + filename)

    return file_write_success

# NOTE: Jun 26, 2014
def create_multiple_files(output_directory, station, station_label, outputs, log, start=None, end=None, other=dict()):
    print 'Station Label: ' + station_label
    station_name = create_station_name(station_label)

    # Check to make sure start value is reasonable
    if start == None or start < station['first_value'] or start > station['end_value']:
        start = station['first_value']

    # Check to make sure end value is reasonable
    if end == None or end > station['end_value'] or end < station['first_value']:
        end = station['end_value']

    # If somehow the values have been swapped, then swap them back
    if start != None and end != None and start > end:
        temp = start
        start = end
        end = temp

    create_decade_files = other['calculate_one_decade'] if 'calculate_one_decade' in other else False
    create_20year_files = other['calculate_two_decade'] if 'calculate_two_decade' in other else False
    create_user_defined_files = other['calculate_custom_range'] if 'calculate_custom_range' in other else False
    user_defined_range = other['custom_range'] if 'custom_range' in other else 0

    successful_file_writes = list()
    for model in outputs:
        if not log:
            print('Outputting model: ' + model)
        if model == 'all':
            model_name = ''
        else:
            model_name = '_' + create_model_name(model)
        base_filename = station_name + model_name
        temp_filename = output_directory + base_filename + '_Temperature.txt'
        precip_filename = output_directory + base_filename + '_Precipitation.txt'

        # Open up the files to write to
        # Start with the temp file
        temp_file_write_success = write_file(temp_filename, station['temp_table'], start, end, outputs[model], log)
        #temp_file_write_success = False
        #temp_file = open(temp_filename, 'w')
        #if not temp_file.closed:
            #if write_table(station['temp_table'], start, end, temp_file, outputs[model]):
                #print 'Finished: ' + temp_filename
                #temp_file_write_success = True
            #else:
                #print 'Failed: ' + temp_filename

        # Finish with the precip file
        precip_file_write_success = write_file(precip_filename, station['precip_table'], start, end, outputs[model], log)
        #precip_file_write_success = False
        #precip_file = open(precip_filename, 'w')
        #if not precip_file.closed:
            #if write_table(station['precip_table'], start, end, precip_file, outputs[model]):
                #print 'Finished: ' + precip_filename
                #precip_file_write_success = True
            #else:
                #print 'Failed: ' + precip_filename
                #precip_file_write_success = False

        successful_file_writes.append([[temp_filename, temp_file_write_success], [precip_filename, precip_file_write_success]])

        if create_decade_files:
            year_range = 10

            temp_filename = output_directory + base_filename + '_AvgTemperature_Decades.txt'
            precip_filename = output_directory + base_filename + '_AvgPrecipitation_Decades.txt'

            temp_file_write_success = write_file(temp_filename, station['temp_table'], start, end, outputs[model], log, year_range=year_range)
            precip_file_write_success = write_file(precip_filename, station['precip_table'], start, end, outputs[model], log, year_range=year_range)
            successful_file_writes.append([[temp_filename, temp_file_write_success], [precip_filename, precip_file_write_success]])

        if create_20year_files:
            year_range = 20

            temp_filename = output_directory + base_filename + '_AvgTemperature_20year.txt'
            precip_filename = output_directory + base_filename + '_AvgPrecipitation_20year.txt'

            temp_file_write_success = write_file(temp_filename, station['temp_table'], start, end, outputs[model], log, year_range=year_range)
            precip_file_write_success = write_file(precip_filename, station['precip_table'], start, end, outputs[model], log, year_range=year_range)
            successful_file_writes.append([[temp_filename, temp_file_write_success], [precip_filename, precip_file_write_success]])

        if create_user_defined_files:
            year_range = user_defined_range

            temp_filename = output_directory + base_filename + '_AvgTemperature_' + str(year_range) + 'year.txt'
            precip_filename = output_directory + base_filename + '_AvgPrecipitation_' + str(year_range) + 'year.txt'

            temp_file_write_success = write_file(temp_filename, station['temp_table'], start, end, outputs[model], log, year_range=year_range)
            precip_file_write_success = write_file(precip_filename, station['precip_table'], start, end, outputs[model], log, year_range=year_range)
            successful_file_writes.append([[temp_filename, temp_file_write_success], [precip_filename, precip_file_write_success]])


    return successful_file_writes

def break_out_params(filename, delimiter):
    station = None
    model = None
    era = None
    model_run = None
    # Check if a Unix style directory is prepended to the filename
    dir_index = filename.rindex('/')
    # Otherwise, check if a Windows style directory is prepended to the filename
    if dir_index != -1:
        filename = filename[dir_index+1:]

    try:
        index1 = 0
        index2 = filename.index(delimiter)
        #print str(index1) + ' ' + str(index2)
        station = filename[index1:index2]
        station = create_station_name(station)
        index1 = index2 + 1
        index2 = index1 + filename[index1:].index(delimiter)
        #print str(index1) + ' ' + str(index2)
        model = filename[index1:index2]
        model = create_model_name(model)
        index1 = index2 + 1
        index2 = index1 + filename[index1:].index(delimiter)
        index2 = index1 + filename[index1:].index(delimiter)
        #print str(index1) + ' ' + str(index2)
        era = filename[index1:index2]
        index1 = index2 + 1
        index2 = index1 + filename[index1:].index(delimiter)
        model_run = filename[index1:index2]
        model_run = create_model_run_name(model_run)
    except:
        # Return nothing to indicate that the input filename does not match the required format
        return None

    return {'Station': station, 'Model': model, 'Era': era, 'Run': model_run}

def create_plot_title(filename, log):
    slash_index = 0
    underscore1_index = 0
    underscore2_index = 0
    dot_index = 0
    try:
        slash_index = filename.rindex('/')
    except ValueError as ve:
        slash_index = 0
        if log:
            pass
    try:
        underscore1_index = slash_index + filename[slash_index+1:].find('_') + 1
    except ValueError as ve:
        underscore1_index = len(filename)
        if log:
            pass
    try:
        underscore2_index = underscore1_index + filename[underscore1_index+1:].find('_') + 1
    except ValueError as ve:
        underscore2_index = len(filename)
        if log:
            pass

    try:
        dot_index = underscore2_index + filename[underscore2_index+1:].find('.') + 1
    except ValueError as ve:
        dot_index = len(filename)
        if log:
            pass

    if underscore2_index >= underscore1_index:
        plot_name = filename[slash_index+1:underscore1_index] + ' ' + filename[underscore1_index+1:underscore2_index] + ' ' + filename[underscore2_index+1:dot_index]
    else:
        plot_name = filename[slash_index+1:underscore1_index] + ' ' + filename[underscore1_index+1:dot_index]

    return plot_name

def get_plot_y_label(filename, log):
    try:
        if filename.find('Temperature') >= 0:
            return 'Temperature in Farenheit'
        elif filename.find('Precipitation') >= 0:
            return 'Precipitation in Inches'
    except ValueError as ve:
        if log:
            pass
    except TypeError as te:
        if log:
            pass
    return 'Unknown'

def get_params(options):

    input_filename = options[0]
    delimiter = options[1]

    params = break_out_params(input_filename, delimiter)

    return params

# NOTE: Jun 26, 2014 - This function extracts a logging parameter
# NOTE: Both the cli and gui call this function.  This is the main entry point for either UI thread to run a paticular job.
def run_job(input_args=dict()):
    # input_directory is the only required parameter.  All others can use default values.
    input_directory = None
    try:
        input_directory = input_args['input_directory']
    except KeyError as ke:
        return [False, None, None]

    if input_directory == None:
        return [False, None, None]

    # NOTE: Jun 26, 2014 - Extract logging parameter here
    log = False if 'log' in input_args and input_args['log'] == False else True
    start_time = None
    # Output logging information
    if log:
        start_time = datetime.datetime.today()
        logging.info('Starting job (' + input_directory + '): ' + str(start_time))

    output_directory = input_args['output_directory'] if 'output_directory' in input_args else None
    individual_files = input_args['individual_files'] if 'individual_files' in input_args else False
    delimiter = input_args['delimiter'] if 'delimiter' in input_args else '.'
    start = input_args['start'] if 'start' in input_args else None
    end = input_args['end'] if 'end' in input_args else None
    other = dict()
    other['calculate_one_decade'] = input_args['calculate_one_decade'] if 'calculate_one_decade' in input_args else False
    other['calculate_two_decade'] = input_args['calculate_two_decade'] if 'calculate_two_decade' in input_args else False
    other['calculate_custom_range'] = input_args['calculate_custom_range'] if 'calculate_custom_range' in input_args else False
    other['custom_range'] = input_args['custom_range'] if 'custom_range' in input_args else 0

    # Output logging information
    if log:
        if 'calculate_one_decade' in other and other['calculate_one_decade']:
            logging.info('Job will create tables using decade averages')
        if 'calculate_two_decade' in other and other['calculate_two_decade']:
            logging.info('Job will create tables using 20 year averages')
        if 'calculate_custom_range' in other and other['calculate_custom_range'] and 'custom_range' in other:
            logging.info('Job will create tables using ' + str(other['custom_range']) + ' year averages')

    try:
        # Replace any common escape sequences that may be confusing the OS interpreter
        input_directory = input_directory.replace('\r', '/r') # carriage return
        input_directory = input_directory.replace('\n', '/n') # line feed
        input_directory = input_directory.replace('\t', '/t') # horizontal tab
        input_directory = input_directory.replace('\b', '/b') # backspace
        input_directory = input_directory.replace('\v', '/v') # vertical tab
        input_directory = input_directory.replace('\f', '/f') # form feed
        input_directory = input_directory.replace('\a', '/a') # bell
        input_directory = input_directory.replace('\e', '/e') # escape
        input_directory = input_directory.replace('\0', '/0') # nul
        # Simplify the input_directory listing (if using Windows)
        input_directory = input_directory.replace('\\', '/')

    except:
        return [False, None, None]

    if not log:
        print('Processing files in directory: ' + input_directory)

    # Create a file listing of what should be read as input
    file_list = build_file_list(input_directory)
    # If no files were generated then return, since the program can't do anything
    if file_list == None:
        if not log:
            print('No file list was built!')
        return [False, None, None]

    # If the output directory does not exist then create a default directory
    if output_directory == None:
        output_directory = get_default_output_directory(input_directory)
    # Also, make sure that the desired output directory exists on the filesystem
    else:
        output_directory = create_output_directory(output_directory)

    # Initialize the variable used for processing
    stations = dict()

    # Process all the files in the file list
    successful_file_reads = list()
    for f in file_list:
        params = get_params([f, delimiter])

        # If this isn't a model file, then skip over it
        if params == None:
            continue

        station_label = params['Station']

        if station_label not in stations:
            stations[station_label] = dict()
        if 'temp_table' not in stations[station_label]:
            stations[station_label]['temp_table'] = dict()
        if 'precip_table' not in stations[station_label]:
            stations[station_label]['precip_table'] = dict()
        if 'outputs' not in stations[station_label]:
            stations[station_label]['outputs'] = dict()
        if 'all' not in stations[station_label]['outputs']:
            stations[station_label]['outputs']['all'] = list()
            stations[station_label]['outputs']['all'].append('year')
        if individual_files and params['Model'] not in stations[station_label]['outputs']:
            stations[station_label]['outputs'][params['Model']] = list()
            stations[station_label]['outputs'][params['Model']].append('year')

        # Create a column name for this file
        col_name = create_column_name(params)

        # Add this file to an output list
        if col_name not in stations[station_label]['outputs']['all']:
            stations[station_label]['outputs']['all'].append(col_name)
        if individual_files and col_name not in stations[station_label]['outputs'][params['Model']]:
            stations[station_label]['outputs'][params['Model']].append(col_name)

        # Calculate the values for the output tables
        successful_file_read = calculate_avgs_for_model(f, stations[station_label], col_name)
        successful_file_reads.append([successful_file_read, f])

        # Output logging information
        if log:
            if successful_file_read:
                logging.info('Successfully read file: ' + f)
            else:
                logging.warn('Failed to read file: ' + f)

    # Finally, create the output files containing the desired data
    successful_file_writes = list()
    for station_label in stations:
        successful_file_write = create_multiple_files(output_directory, stations[station_label], station_label, stations[station_label]['outputs'], log, start, end, other)
        successful_file_writes.append([station_label, output_directory, successful_file_write])

    if log:
        # The time should be calculated for the time taken for each run.  The argument below implies a time
        # differential between the begginning of the program, not the job.  This is an error, which has been corrected.
        #start_time = input_args['start_time'] if 'start_time' in input_args else datetime.datetime.today()
        end_time = datetime.datetime.today()
        logging.info('Ending job (' + input_directory + '): ' + str(end_time))
        if start_time != None:
            logging.info('Total time: ' + str(get_time_diff_secs(start_time, end_time)) + ' seconds.')

    if 'list_text' in input_args:
        return [True, successful_file_reads, successful_file_writes, input_args['list_text']]

    return [True, successful_file_reads, successful_file_writes]

def run_jobs(input_args=list()):
    outcome_list = list()
    successful_jobs = list()
    job_id = None
    log = False if 'log' in input_args and input_args['log'] == False else True

    if not log:
        print('\n')
    else:
        logging.info('\n')
    for job_args in input_args:
        try:
            job_id = job_args['job_id']
            if not log:
                print('Running Job ' + str(job_id))
            else:
                logging.info('Running Job ' + str(job_id))
            outcome = run_job(job_args)
            outcome_list.append(outcome)
            success = outcome[0]
            if not log:
                print('\n')
            else:
                logging.info('\n')
            successful_jobs.append([job_id, success])
        except KeyError as ke:
            successful_jobs.append([job_id, False])
            pass

    # NOTE: This generates a list of successfully written files to be used as inputs for generating graphs
    output_files_list = list()
    for outcome in outcome_list:
        if outcome[0]:
            for output_outcomes in outcome[2]:
                for output_outcome_files in output_outcomes[2]:
                    for output_outcome_file in output_outcome_files:
                        if output_outcome_file[1]:
                            output_files_list.append(output_outcome_file[0])

    # TODO: Add a method to handle the generation of graphs
    create_plots(output_files_list, log)

    return successful_jobs

def create_job_list(options, start_time):
    # Create a list of input arguments for each job.
    input_args = list()
    for job_counter in range(len(options.input_directory)):
        job_args = dict();
        job_args['job_id'] = job_counter
        job_args['delimiter'] = options.delimiter
        job_args['individual_files'] = options.individual_files
        job_args['input_directory'] = options.input_directory[job_counter]
        job_args['output_directory'] = options.output_directory[job_counter] if options.output_directory != None and job_counter < len(options.output_directory) else None
        job_args['start'] = options.beginning_year[job_counter] if options.beginning_year != None and job_counter < len(options.beginning_year) else None
        job_args['end'] = options.ending_year[job_counter] if options.ending_year != None and job_counter < len(options.ending_year) else None
        job_args['log'] = False if options.log != None and not options.log else True
        job_args['start_time'] = start_time
        input_args.append(job_args)
    return input_args

def create_plots(output_files_list, log, gui_frame=None):
    #print 'Number of plots in output: ' + str(len(output_files_list))

    for output_file_and_job in output_files_list:
        output_file = output_file_and_job[0]
        # NOTE: Skip files with "Avg" in the filename.  The problem occurs when creating line graphs with intervals like:
        # 1950-1959, 1951-1960, 1952-1961, etc.  This is because the y-value is a range associated with a discrete range of data,
        # but not a continuous range.  Would a bar chart be more applicable?
        if output_file.find('Avg') != -1:
            continue

        if log:
            logging.info('Creating plots for file: ' + output_file)
        else:
            print('Creating plots for file: ' + output_file)

        #(df, df_closest_fit) = ModelRunnerPlots.create_dataframes(output_file, log)
        datatype = output_file[output_file.rindex('_')+1:output_file.rindex('.')]
        df = ModelRunnerPlots.create_dataframes(output_file, datatype, log)
        plot_title = create_plot_title(output_file, log)
        window_title = None
        if len(output_file_and_job) == 2:
            window_title = create_plot_title(output_file, log) + ': ' + output_file_and_job[1]
        else:
            window_title = plot_title

        if log:
            logging.info('Plot Title: ' + plot_title)

        all_plot = ModelRunnerPlots.create_line_plot(plot_title, get_plot_y_label(output_file, log), df, log, value_vars=list(df.columns - ['year']))
        #closest_fit_plot = ModelRunnerPlots.create_line_plot(create_plot_title(output_file, log) + ' Closest Fit', get_plot_y_label(output_file, log), df_closest_fit, log, value_vars=list(df_closest_fit.columns - ['year']))

        # Create two instances of graph windows for each graph
        if gui_frame != None:
            #plot_title = create_plot_title(output_file, log)
            y_label = get_plot_y_label(output_file, log)
            #all_plot_gui = ModelRunnerGraphGUI.GraphWindow(parent=None, df=df, plot=all_plot, plot_title=plot_title, y_label=y_label)
            #closest_fit_plot_gui = ModelRunnerGraphGUI.GraphWindow(parent=None, df=df_closest_fit, plot=closest_fit_plot, plot_title=plot_title + ' Closest Fit', y_label=y_label)
            gui_frame.add_plot({'df': df, 'plot': all_plot, 'plot_title': plot_title, 'y_label': y_label, 'window_title': window_title, 'output_file': output_file})
            #print 'Adding plots'

        # Or, just save the files if a GUI is not being used
        else:
            plot_base_fname = output_file[0:output_file.rindex('.')]
            all_plot_fname = plot_base_fname + '_all_plot.png'
            all_plot.savefig(all_plot_fname, format='png')
            if log:
                logging.info('Created a plot file of all output columns called ' + all_plot_fname)

            closest_fit_plot_fname = plot_base_fname + '_closest_fit_plot.png'
            closest_fit_plot.savefig(closest_fit_plot_fname, format='png')
            if log:
                logging.info('Created a plot file of the best fitting output called ' + closest_fit_plot_fname)

def main(argv):
    parser = OptionParser(version = __VERSION__)
    parser.prog = 'Model Runner'
    parser.description = 'This program runs a batch job on a directory containing output files from Big Horn.' + \
                         'The input data files can describe a historical data set or future model prediction data set.' + \
                         'The program outputs a set of averages of temperature and sums of precipitation respectively for ' + \
                         'the historical or furture data sets.  The output files contain these attributes from different of ' + \
                         'of their respective models.  The output files are marked in the following format:\n' + \
                         'Temp_STATION_MODEL_MODELTYPE_Etc.txt - for temperatures\n' + \
                         'Precip_STATION_MODEL_MODELTYPE_Etc.txt - for precipitation\n'

    parser.add_option("-i", "--input_directory", action='append', dest="input_directory", help="directory to search for input files", type=str)
    parser.add_option("-o", "--output_directory", action='append', dest="output_directory", help="directory search for output files", type=str)
    parser.add_option("-d", "--delimiter", dest="delimiter", help="the delimiter to break out the parameters (default='.')", type=str, default='.')
    parser.add_option("-g", "--nogui", action="store_true", help="the flag that determines whether a gui should not be used")
    parser.add_option("-f", "--individual_files", action="store_true", dest='individual_files', help="flag that determines whether individual models files should be created (true) or not (false)")
    parser.add_option("-b", "--beginning_year", action='append', dest="beginning_year", help="the beginning year of the output", type=int)
    parser.add_option("-e", "--ending_year", action='append', dest="ending_year", help="the ending year of the output", type=int)
    # TODO: Implement a logger for debugging purposes
    parser.add_option("-l", "--log", action="store_true", dest='log', help="flag that determines whether to create and write to a debug log file", default=True)
    options, args = parser.parse_args(argv)

    start_time = None
    if options.log:
        start_time = datetime.datetime.today()
        log_filename_prefix = '{0:02}_{1:02}_{2:02}_{3:02}_{4:02}_{5:02}_'.format(start_time.hour, start_time.minute, start_time.second, start_time.month, start_time.day, start_time.year)
        log_filename = log_filename_prefix + 'model_runner_debug.log'
        # Add log filename to options so it can be retrieved later
        log_handler = logging.FileHandler(log_filename, mode='w')
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(20) # Setting the logging level to output information messages (level = 20)
        logging.info('Program started: ' + str(start_time))

    if options.nogui:
        # Input directory is the only required parameter.
        if options.input_directory == None:
            print(parser.prog + ' ' + parser.version)
            parser.print_help()
            return

        else:
            input_args = create_job_list(options, start_time)
            run_jobs(input_args)

    else:
        # Create the main window
        root = Tkinter.Tk()
        root.title(parser.prog + ' ' + parser.version)

        # Create the widgets for organizing the file processing

        # NOTE: I'm testing the capability of using an image icon on a GUI button
        add_icon_filename = 'plus.gif'
        add_icon_directory = os.getcwd() + '/resources/images/'

        if os.path.isdir(add_icon_directory):
            add_icon_filename = add_icon_directory + add_icon_filename
        if not os.path.isfile(add_icon_filename):
            add_icon_filename = None

        job_list = ModelRunnerGUI.JobList(parent=root, add_icon_filename=add_icon_filename, run_job=run_job, create_plots=create_plots, log_filename=log_filename)
        job_list.set_grid()

        # Run the window main loop
        root.mainloop()

    if options.log:
        end_time = datetime.datetime.today()
        logging.info('Program ended: ' + str(end_time))
        if start_time != None:
            logging.info('Total time: ' + str(get_time_diff_secs(start_time, end_time)) + ' seconds.')
        logging.shutdown()

if __name__ == '__main__':
    main(sys.argv)
