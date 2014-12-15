#! /usr/bin/env python

'''
Test program for using the ModelRunnerPlots module
'''

# Matplotlib, and by extension ggplot, automatically generate GUIs which conflict with the GUI implementation
# defined here.  So, we need to "suppress" this inclination via the following statements.
import matplotlib as mpl
mpl.use('Agg')

import ModelRunnerPlots
import ModelRunnerGraphGUI

import os
import sys
import string
from optparse import OptionParser
import logging
import datetime
import time

import Tkinter
import ttk

def main(argv):
    # Create an OptionParser for reading optional parameters
    parser = OptionParser(version='0.10')
    parser.prog = 'Model Runner Plots Test'

    print 'Running ' + parser.prog + ' ' + parser.version

    options, args = parser.parse_args(argv)

    log = False

    # Use a hardcoded value for the input filename, probably adding in an option argument later
    # for more flexibility
    filename = 'output_test/BigHorn_Temperature.txt'

    # Create the data frames and plots from the input file
    (df, df_closest_fit) = ModelRunnerPlots.create_dataframes(filename, log)
    # Get the plot and create a matplotlib figure.

    df_plot = ModelRunnerPlots.create_line_plot('Temperature', 'Temperature in Farenheit', df=df, log=log, value_vars=list(df.columns - ['year']))
    df_plot.savefig('graph_test.png', format='png')

    # Create our GUI componenets.  Note, the data frame and plot must be created beforehand for the GUI to work properly.
    root = Tkinter.Tk()
    root.title(parser.prog + ' ' + parser.version)
    root.grid()

    model_runner_gui = ModelRunnerGraphGUI.GraphFrame(root, df=df, plot=df_plot)
    model_runner_gui.set_grid()

    # Run the window main loop
    root.mainloop()

if __name__ == '__main__':
    main(sys.argv)