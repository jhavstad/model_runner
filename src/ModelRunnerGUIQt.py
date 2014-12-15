#! /usr/bin/env python

import sys
import os

from PyQt5.QtCore import QEvent, QObject, pyqtSignal, QDir, QThread, QSize
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QApplication, QWidget, QProgressDialog, QMessageBox, QFileDialog, QLineEdit, QSpinBox, QLabel
from PyQt5.QtGui import QMouseEvent, QDrag
from PyQt5.Qt import Qt

import PyQtExtras
import PyQtDnd

from threading import Thread

class PlotReadyEvent(QEvent):
    event_type = 2002

    def __init__(self):
        QEvent.__init__(self, 2002)
        self.registerEventType(self.event_type)

    def get_event_type():
        return 2002

class JobDoneEvent(QEvent):
    event_type = 2000

    def __init__(self):
        QEvent.__init__(self, 2000)
        self.registerEventType(self.event_type)

    def get_event_type():
        return 2000

class JobUpdateEvent(QEvent):
    event_type = 2001

    def __init__(self):
        QEvent.__init__(self, 2001)
        self.registerEventType(self.event_type)

    def get_event_type():
        return 2001


class JobList(QFrame):

    def __init__(self, **kwargs):
        QFrame.__init__(self)

        if 'window_title' in kwargs:
            self.setWindowTitle(kwargs['window_title'])

        self.parent_frame_layout = QVBoxLayout(self)

        self.job_list_scroll_area_frame = QFrame()

        self.job_list_scroll_area = PyQtExtras.ListScrollArea(self.job_list_scroll_area_frame)

        self.parent_frame_layout.addWidget(self.job_list_scroll_area_frame)

        self.job_button_frame_layout = QHBoxLayout()

        # Add and Remove Jobs Buttons
        self.remove_job_button = PyQtExtras.CommandButton(parent=None, text='Remove Job')
        self.remove_job_button.set_handler(self.on_remove)

        self.add_job_button = PyQtExtras.CommandButton(parent=None, text='Add Job')
        self.add_job_button.set_handler(self.on_add)

        self.job_button_frame_layout.addWidget(self.remove_job_button)
        self.job_button_frame_layout.addWidget(self.add_job_button)
        self.job_button_frame_layout.setAlignment(Qt.AlignRight)

        self.parent_frame_layout.addLayout(self.job_button_frame_layout)

        # Process and Close Buttons
        self.close_button_frame_layout = QHBoxLayout()

        self.close_button = PyQtExtras.CommandButton(parent=None, text='Quit')
        self.close_button.set_handler(self.on_close)

        self.process_jobs_button = PyQtExtras.CommandButton(parent=None, text='Start')
        self.process_jobs_button.set_handler(self.on_process_jobs)

        self.close_button_frame_layout.addWidget(self.close_button)
        self.close_button_frame_layout.addWidget(self.process_jobs_button)
        self.close_button_frame_layout.setAlignment(Qt.AlignRight)

        self.parent_frame_layout.addLayout(self.close_button_frame_layout)

        # Add a progress dialog
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.hide()

        # Create instance variables
        self.run_job = kwargs['run_job'] if 'run_job' in kwargs else None

        self.create_plots = kwargs['create_plots'] if 'create_plots' in kwargs else None

        self.log_filename = kwargs['log_filename'] if 'log_filename' in kwargs else None

        # Create some variables that keep track of the job progress while the background thread is running
        self.current_job_status = None
        self.current_job_step = None
        self.current_job_line = None
        self.current_job_outcomes = list()
        self.jobs_thread = None
        self.plots_thread = None
        self.job_outcomes = None

        # Create a Frame for selecting the plots to display
        self.dnd_graphs_frame = None

        self.reinit_variables()

        # Set a minimum size for viewing
        self.setMinimumSize(QSize(800, 640))

    def reinit_variables(self):
        self.job_params = dict()

        self.last_job_id = -1

        #self.job_outcomes = list()

        self.plot_args = list()

        self.on_button = False

    def add_job_params(self, input_args):
        self.job_params = input_args
        # Add each element to the job list
        for job in self.job_params:
            self.add_job(job)

    def add_job(self, job):
        try:
            index_end = job['input_directory'].rindex('/')
            index_start = job['input_directory'].rindex('/', 0, index_end)
            input_directory_text = job['input_directory']
            list_text = 'Job ' + str(job['job_id']) + ' \'' + input_directory_text + '\''
            if job['start'] != None:
                list_text += ' ' + str(job['start'])
                if job['end'] != None:
                    list_text += ' to'
            if job['end'] != None:
                list_text += ' ' + str(job['end'])

            if job['job_id'] > self.last_job_id:
                self.last_job_id = job['job_id']

            # Add the list text to the job params as an optional parameter to read later to display in a future Graph GUI (or for any other useful purpose)
            job['list_text'] = list_text

            # The line number is used wrt the GUI to indicate which job in the job list is being currently executed.
            job['line_number'] = self.job_list_scroll_area.get_num_items() - 1

            self.job_params[job['job_id']] = job

            # Add the text to the listview
            self.job_list_scroll_area.add_item_by_string(list_text)

        except KeyError as ke:
            # Should show some error message indicating that there is a problem.
            pass

    def ask_to_clear_jobs(self):
        print('Asking to clear jobs')
        for job in self.job_params.itervalues():
            line_number = job['line_number']
            # TODO: Set text item to black

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Jobs Finished')
        msg_box.setText('All jobs have been completed.')
        msg_box.setInformativeText('Would you like to clear the job list?')
        msg_box.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msg_box.setDefaultButton(QMessageBox.Yes)

        answer = msg_box.exec_()

        if answer == QMessageBox.Yes:
            self.clear_list()

        self.ask_to_plot_graphs()

    def ask_to_plot_graphs(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle('Plot Graphs')
        msg_box.setText('Ready to plot graphs.')
        msg_box.setInformativeText('Do you want to create graph plots of the data?')
        msg_box.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msg_box.setDefaultButton(QMessageBox.Yes)

        answer = msg_box.exec_()

        if answer == QMessageBox.No:
            return

        if self.create_plots != None:
            output_files_list = list()
            print('Number of job outcomes: ' + str(len(self.job_outcomes)))
            for job_outcome in self.job_outcomes:
                for output_outcomes in job_outcome[2]:
                    (station, output_directory, output_files) = output_outcomes
                    for output_files_tuple in output_files:
                        for output_file_tuple in output_files_tuple:
                            (output_file, output_file_success) = output_file_tuple
                            if output_file_success:
                                print('Found an output file that has been successfully created!')
                                # If there is a list text variable (the 4th (or 3rd by 0 based index) variable), then add it to our output list
                                if len(job_outcome) == 4:
                                    output_files_list.append([output_file, job_outcome[3]])
                                else:
                                    output_files_list.append([output_file])

            self.plots_thread = PlotsThread(self.create_plots, output_files_list, self)
            self.plots_thread.start()

    def add_plot(self, args=dict()):
        self.plot_args.append(args)

    def create_plot_gui(self):
        self.dnd_graphs_frame = PyQtDnd.DualFrame('Drag and Drop Output Plots', self.finish_creating_plot_gui, False)
        for args in self.plot_args:
            graph_name = args['output_file']
            self.dnd_graphs_frame.add_to_first(graph_name)
            print('Added graph: ' + graph_name)

        self.dnd_graphs_frame.show()
        print('Dnd plot frame shown')

    def finish_creating_plot_gui(self, plot_labels):
        graph_count = 1
        for plot_label in plot_labels:
            for args in self.plot_args:
                #print 'Looking in ' + args['plot_title'] + ' for ' + plot_label
                #print 'The plot label is: ' + plot_label
                #print 'The output file is: ' + args['output_file']
                if plot_label == args['output_file']:
                    #print 'Creating graph ' + str(graph_count)
                    graph_count += 1
                    # TODO: Create a Qt Version of the ModelRunnerGraphGUI
                    #graph_window = ModelRunnerGraphGUI.GraphWindow(parent=self, title=args['window_title'], df=args['df'], plot=args['plot'], plot_title=args['plot_title'], y_label=args['y_label'], log_filename=self.log_filename)

        # Have to clear out list here instead of clear_list because clear_list() removes plot_args before this method has a chance to read
        # them and create the appropriate plot graph windows
        self.reinit_variables()

    # Clear all the elements in the list
    def clear_list(self):

        # Save plot args because they are need later in this run
        #plot_args = self.plot_args
        self.reinit_variables()
        # Restore the plot args
        #self.plot_args = plot_args

        self.job_list_scroll_area.clear_all()

    def on_add(self):
        # TODO: Create an instance of JobParameters
        JobParameters(parent=self.parent, beginning_year=1950, ending_year=2100, job_id=self.last_job_id + 1, entry=self).show()
        print('Adding job')

    def on_remove(self):

        line_text = self.job_list_scroll_area.get_currently_selected_item()
        job_id = int(line_text[4:line_text.index(' ', 4)])
        job = self.job_params.pop(job_id)
        self.job_list.delete(line_number)
        print('Removed Job ' + str(job['job_id']))

        # Fix line number
        for line_number in range(self.job_list_scroll_area.get_num_items()):
            line_text = self.job_list_scroll_area.get_item(line_number)
            job_id = int(line_text[4:line_text.index(' ', 4)])
            #print 'Job ' + str(job_id) + ' is now on line ' + str(line_number)
            self.job_params[job_id]['line_number'] = line_number

        print('Removing job')

    def on_close(self):
        self.hide()

        QApplication.exit(0)

    def on_process_jobs(self):
       self.start_jobs()

    def start_jobs(self):
        print('Starting jobs')

        # If there are no queued jobs then simply return
        if len(self.job_params) == 0 or self.job_list_scroll_area.get_num_items() == 0:
            return

        # Deactivate the process button
        self.process_jobs_button.setDisabled(True)

        # Initialize the progress bar
        self.progress_dialog.setValue(0)
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()

        # Set the cursor to be a Wait Cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)

        # Start process thread
        self.jobs_thread = JobsThread(self.job_params, self.run_job, self.on_update, self.on_resume)
        self.jobs_thread.start()

    def on_update(self, status, line_number, step):
        self.current_job_status = status
        self.current_job_line = line_number
        self.current_job_step = step

        QApplication.postEvent(self, JobUpdateEvent())

    def update_progress(self, status, line_number, step):
        if status == 'init':
            # TODO: Set text color to green and focus in on current item
            pass
        elif status == 'success':
            # TODO: Set text color to blue
            pass
        elif status == 'fail':
            # TODO: Set text color to red
            pass

        self.progress_dialog.setValue(self.progress_dialog.value() + step)

    def on_resume(self, job_outcomes=list()):
        print('Received ' + str(len(job_outcomes)) + ' from Jobs thread')

        self.current_job_outcomes = job_outcomes

        QApplication.postEvent(self, JobDoneEvent())


    def resume(self, job_outcomes=list()):
        self.progress_dialog.setValue(100)
        self.progress_dialog.setModal(False)
        self.progress_dialog.hide()

        self.job_outcomes = job_outcomes

        print('Ready to resume processing ' + str(len(self.job_outcomes)) + ' from Jobs thread')

        self.process_jobs_button.setEnabled(True)

        QApplication.setOverrideCursor(Qt.ArrowCursor)

        self.ask_to_clear_jobs()

    def finished_adding_plots(self):
        QApplication.postEvent(self, PlotReadyEvent())

    def event(self, e):
        if e.type() == JobDoneEvent.event_type:
            print('Received JobDoneEvent')
            print('Number of saved job outcomes: ' + str(len(self.current_job_outcomes)))
            self.resume(self.current_job_outcomes)
            return True
        elif e.type() == JobUpdateEvent.event_type:
            print('Received JobUpdateEvent')
            self.update_progress(self.current_job_status, self.current_job_line, self.current_job_step)
            return True
        elif e.type() == PlotReadyEvent.event_type:
            print('Received PlotReadyEvent')
            self.create_plot_gui()
            return True;
        return QFrame.event(self, e)

class JobParameters(QFrame):
    def __init__(self, **kwargs):
        QFrame.__init__(self)

        self.setWindowTitle('Job Parameters')

        self.main_layout = QVBoxLayout(self)

        # Create the Input and Output Browser buttons
        self.output_directory_selector = DirectorySelector(self, 'Output Directory:')
        self.input_directory_selector = DirectorySelector(self, 'Input Directory:', send_to_other=lambda f, x: f(x + '/output/'), other=self.output_directory_selector.set_dir)

        # Create the Begin and End year selectors
        self.beginning_year = kwargs['beginning_year'] if 'beginning_year' in kwargs else 1950
        self.ending_year = kwargs['ending_year'] if 'ending_year' in kwargs else 2100
        self.beginning_year_selector = YearSelector(text='Beginning Year:', min_year=self.beginning_year, max_year=self.ending_year)
        self.beginning_year_selector.set_year(self.beginning_year)
        self.ending_year_selector = YearSelector(text='Ending Year:', min_year=self.beginning_year, max_year=self.ending_year)
        self.ending_year_selector.set_year(self.ending_year)

        # Create the Range Year CheckBoxes
        self.one_decade_range_selector = PyQtExtras.CommandCheckBox('Calculate 10 Year Range')
        self.one_decade_range_selector.set_handlers(self.on_one_decade_range_checked, self.on_one_decade_range_unchecked)
        self.one_decade_range_selector.set_state(False)
        self.two_decade_range_selector = PyQtExtras.CommandCheckBox('Calculate 20 Year Range')
        self.two_decade_range_selector.set_handlers(self.on_two_decade_range_checked, self.on_two_decade_range_unchecked)
        self.two_decade_range_selector.set_state(False)
        self.custom_range_frame = QFrame()
        self.custom_range_layout = QHBoxLayout(self.custom_range_frame)
        self.custom_range_selector = PyQtExtras.CommandCheckBox('Calculate Custom Year Range')
        self.custom_range_selector.set_handlers(self.on_custom_range_checked, self.on_custom_range_unchecked)
        self.custom_range_selector.set_state(False)
        self.custom_range_input_text = PyQtExtras.NumberEdit(max_length=3)
        self.custom_range_input_text.setDisabled(True)
        self.custom_range_layout.addWidget(self.custom_range_selector)
        self.custom_range_layout.addWidget(self.custom_range_input_text)

        # Create the button layout and the corresponding buttons
        self.button_frame = QFrame()
        self.button_layout = QHBoxLayout(self.button_frame)
        self.cancel_button = PyQtExtras.CommandButton('Cancel')
        self.cancel_button.set_handler(self.on_close)
        self.ok_button = PyQtExtras.CommandButton('OK')
        self.ok_button.set_handler(self.on_submit)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.setAlignment(Qt.AlignRight)

        # Add everything to the main layout
        self.main_layout.addWidget(self.input_directory_selector)
        self.main_layout.addWidget(self.output_directory_selector)
        self.main_layout.addWidget(self.beginning_year_selector)
        self.main_layout.addWidget(self.ending_year_selector)
        self.main_layout.addWidget(self.one_decade_range_selector)
        self.main_layout.addWidget(self.two_decade_range_selector)
        self.main_layout.addWidget(self.custom_range_frame)
        self.main_layout.addWidget(self.button_frame)

        self.job_id = kwargs['job_id'] if 'job_id' in kwargs else None
        self.entry = kwargs['entry'] if 'entry' in kwargs else None

        self.one_decade_range_selected = False
        self.two_decade_range_selected = False
        self.custom_range_selected = False

    def on_one_decade_range_checked(self):
        self.one_decade_range_selected = True

    def on_one_decade_range_unchecked(self):
        self.one_decade_range_selected = False

    def on_two_decade_range_checked(self):
        self.two_decade_range_selected = True

    def on_two_decade_range_unchecked(self):
        self.two_decade_range_selected = False

    def on_custom_range_checked(self):
        self.custom_range_selected = True
        self.custom_range_input_text.setEnabled(True)

    def on_custom_range_unchecked(self):
        self.custom_range_selected = False
        self.custom_range_input_text.setDisabled(True)

    def on_submit(self):
        job = dict()
        job['job_id'] = self.job_id
        job['delimiter'] = '.'
        job['individual_files'] = False
        job['input_directory'] = self.input_directory_selector.get_dir()
        job['output_directory'] = self.output_directory_selector.get_dir()
        job['start'] = self.beginning_year_selector.get_selected_year()
        job['end'] = self.ending_year_selector.get_selected_year()
        job['calculate_one_decade'] = self.one_decade_range_selected
        job['calculate_two_decade'] = self.two_decade_range_selected
        job['calculate_custom_range'] = self.custom_range_selected
        job['custom_range'] = int(self.custom_range_selected)
        job['log'] = True

        if self.entry != None:
            self.entry.add_job(job)
        self.on_close()

    def on_close(self):
        self.hide()
        self.destroy()

class YearSelector(QFrame):
    def __init__(self, text='Year:', min_year=1950, max_year=2100, **kwargs):
        QFrame.__init__(self)
        self.main_layout = QHBoxLayout(self)
        self.label = QLabel(text)
        self.year_selector = QSpinBox()
        self.year_selector.setRange(min_year, max_year)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.year_selector)

    def get_selected_year(self):
        return self.year_selector.value()

    def set_year(self, year):
        self.year_selector.setValue(int(year))


class DirectorySelector(QFrame):
    def __init__(self, parent, label_text, send_to_other=None, other=None):
        QFrame.__init__(self)

        self.parent = parent
        self.send_to_other = send_to_other
        self.other = other

        self.input_dir = None

        # Create the GUI widgets
        self.main_layout = QHBoxLayout(self)
        self.label = QLabel(label_text)
        self.dir_entry = QLineEdit()
        self.browse_button = PyQtExtras.CommandButton('Browse')
        self.browse_button.set_handler(self.on_browse)

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.dir_entry)
        self.main_layout.addWidget(self.browse_button)

    def on_browse(self):
        print('Browsing for directory')
        directory = QFileDialog(self.parent).getExistingDirectory()
        if directory != None:
            self.input_dir = str(directory)
            self.dir_entry.clear()
            self.dir_entry.insert(self.input_dir)
            if self.other != None and self.send_to_other != None:
                self.send_to_other(self.other, self.input_dir)

    def get_dir(self):
        document_text = self.dir_entry.text()
        # Make sure the instance variable for the current text and the text inside the entry field match
        if document_text != self.input_dir:
            self.input_dir = document_text
        return self.input_dir

    def set_dir(self, input_dir):
        self.input_dir = input_dir
        self.dir_entry.clear()
        self.dir_entry.insert(self.input_dir)

class PlotsThread(QThread):
    '''
    create_plots is the function to call to read plotting tables and generate ggplot/matplotlib plot figures
    output_files_list is the list containing the output files containing plotting data tables
    parent is the root widget to send events to when the creation has been completed
    '''

    def __init__(self, create_plots, output_files_list, parent):
        QThread.__init__(self)
        self.create_plots = create_plots
        self.output_files_list = output_files_list
        self.parent = parent

    def run(self):
        self.create_plots(self.output_files_list, log=True, gui_frame=self.parent)
        self.parent.finished_adding_plots()

class JobsThread(QThread):
    '''
    job_params is a dictionary of input arguments to pass to the program for running the job
    run_job is the function to call to start processing a job
    on_update is the function to call to update the UI when a job reates a milestone
    on_resume is the function to call when the job processing must continue
    '''

    def __init__(self, job_params, run_job=None, on_update=None, on_resume=None):
        QThread.__init__(self)
        self.job_params = job_params
        self.run_job = run_job
        self.on_update = on_update
        self.on_resume = on_resume

    def run(self):
        self.run_jobs()

    def run_jobs(self):
        step_val = int(100.0 / float(len(self.job_params)))
        step = 0
        job_outcomes = list()
        for job in self.job_params.itervalues():
            line_number = job['line_number']
            self.on_update('init', line_number, step)
            # Here is where the job is executed in the main program thread (behind the scenes wrt the UI)
            success = False
            if self.run_job != None:
                success = self.run_job(job)
            step += step_val
            if success:
                self.on_update('success', line_number, step)
            else:
                self.on_update('fail', line_number, step)
            job_outcomes.append(success)

        print('Ran ' + str(len(job_outcomes)) + ' jobs')
        self.on_resume(job_outcomes)

def main(argv):
    app = QApplication([])

    job_list = JobList(window_title='Sample Job List')

    job_list.show()

    app.exec_()

if __name__ == '__main__':
    main(sys.argv)
