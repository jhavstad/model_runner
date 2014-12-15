'''

'''

from ttk import Frame
from ttk import Button
from ttk import Entry
from ttk import Label
from ttk import Scrollbar
from ttk import Progressbar
from ttk import Checkbutton

from Tkinter import Listbox
from Tkinter import Toplevel
from Tkinter import Spinbox
from Tkinter import StringVar
from Tkinter import IntVar
from Tkinter import PhotoImage

import Tkinter

import tkFileDialog
import tkMessageBox as msg

from threading import Thread

import ModelRunnerGraphGUI

import Dnd

class JobList(Frame):
    # NOTE: job_params contains information about a Job in the Joblist
    # NOTE: plot_args contains information about plotting information, which occurs after the jobs have been and the data files have been created

    def __init__(self, parent=None, **kwargs):
        Frame.__init__(self, parent)
        self.parent = parent
        self.job_list_yscroll = Scrollbar(self, orient=Tkinter.VERTICAL)
        self.job_list_xscroll = Scrollbar(self, orient=Tkinter.HORIZONTAL)
        self.job_list = Listbox(self, xscrollcommand=self.job_list_xscroll, yscrollcommand=self.job_list_yscroll)
        self.job_list_xscroll['command'] = self.job_list.xview
        self.job_list_yscroll['command'] = self.job_list.yview
        self.new_job_frame = Frame(self)
        add_icon_filename = kwargs['add_icon_filename'] if 'add_icon_filename' in kwargs else None
        if add_icon_filename == None:
            self.add_job_button = Button(self.new_job_frame, text='Add Job', command=self.on_add)
        else:
            add_icon = PhotoImage(file=add_icon_filename)
            self.add_job_button = Button(self.new_job_frame, text='Add Job', compound='bottom', image=add_icon, command=self.on_add)
        self.remove_job_button = Button(self.new_job_frame, text='Remove Job', command=self.on_remove)
        self.progress_frame = Frame(self)
        self.progress_value = Tkinter.IntVar()
        self.progress_bar = Progressbar(self.progress_frame, variable=self.progress_value)
        self.button_frame = Frame(self)
        self.process_button = ProcessButton(parent=self.button_frame, start_jobs=self.start_jobs)
        self.quit_button = QuitButton(parent=self.button_frame, close_other_windows=self.close_top_level_windows)

        self.run_job = kwargs['run_job'] if 'run_job' in kwargs else None

        self.create_plots = kwargs['create_plots'] if 'create_plots' in kwargs else None

        self.log_filename = kwargs['log_filename'] if 'log_filename' in kwargs else None

        self.bind('<<AskToClearJobs>>', self.ask_to_clear_jobs)
        self.bind('<<AskToPlotGraphs>>', self.ask_to_plot_graphs)
        self.bind('<<CreatePlotGUI>>', self.create_plot_gui)
        self.parent.bind('<ButtonPress>', self.on_press)
        self.parent.bind('<Configure>', self.on_resize)

        self.reinit_variables()

        self.top_level_windows = list()

        # NOTE: Because there seems to be an issue resizing child widgets when the top level (Tk) widget is being resized,
        # the resize option will be disabled for this window
        self.parent.resizable(width=False, height=False)

        self.lift()

    def reinit_variables(self):
        self.job_params = dict()

        self.last_job_id = -1

        self.job_outcomes = list()

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

            self.job_list.insert(Tkinter.END, list_text)

            # Add the list text to the job params as an optional parameter to read later to display in a future Graph GUI (or for any other useful purpose)
            job['list_text'] = list_text

            # The line number is used wrt the GUI to indicate which job in the job list is being currently executed.
            job['line_number'] = self.job_list.size() - 1
            #print str(job['line_number'])

            self.job_params[job['job_id']] = job
        except KeyError as ke:
            # Should show some error message indicating that there is a problem.
            pass

        #print str(self.job_params)
        #print 'Added Job ' + str(job['job_id'])

    def ask_to_clear_jobs(self, event):
        for job in self.job_params.itervalues():
            line_number = job['line_number']
            self.job_list.itemconfig(line_number, foreground='black')

        # Update parent to refresh widget appearance
        self.parent.update()

        # Reactivate process button
        self.process_button.config(state = Tkinter.NORMAL)

        # Note: Display a pop-up that tells the user that the job is done and asks if the job list should be cleared.

        clearList = msg.askyesno(title='Jobs Finished', message='All jobs have been completed.  Would you like to clear the job list?', master=self)
        if clearList:
            self.clear_list()

    def ask_to_plot_graphs(self, event):
        # TODO: Add a dialog that also asks to create a graph of the 'Other Type Of Plot'
        plotGraphs = msg.askyesno(title='Plot Graphs', message='Create plots of data?', master=self)

        if not plotGraphs:
            return

        # TODO: Iterate through the jobs to display to the user an interface that asks if they want to graphs of the outputs
        if self.create_plots != None:
            output_files_list = list()
            for job_outcome in self.job_outcomes:
                for output_outcomes in job_outcome[2]:
                    (station, output_directory, output_files) = output_outcomes
                    for output_files_tuple in output_files:
                        for output_file_tuple in output_files_tuple:
                            (output_file, output_file_success) = output_file_tuple
                            if output_file_success:
                                # If there is a list text variable (the 4th (or 3rd by 0 based index) variable), then add it to our output list
                                if len(job_outcome) == 4:
                                    output_files_list.append([output_file, job_outcome[3]])
                                else:
                                    output_files_list.append([output_file])

            plots_thread = PlotsThread(self.create_plots, output_files_list, self)
            plots_thread.start()

    def add_plot(self, args=dict()):
        self.plot_args.append(args)

    def finished_adding_plots(self):
        self.event_generate('<<CreatePlotGUI>>', when='tail')

    def create_plot_gui(self, event):
        # TODO: This should be replaced with a new window that allows the user to drag and drop the icons from one frame to another
        graph_names = list()
        for args in self.plot_args:
            graph_name = args['output_file']
            graph_names.append(graph_name)
        dnd_graphs_frame = Dnd.createFrame(self, 'Drag and Drop Output Plots', graph_names, self.finish_creating_plot_gui)

    # This is the entry point for the
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
                    graph_window = ModelRunnerGraphGUI.GraphWindow(parent=self, title=args['window_title'], df=args['df'], plot=args['plot'], plot_title=args['plot_title'], y_label=args['y_label'], log_filename=self.log_filename)
                    graph_window.set_grid()
                    self.top_level_windows.append(graph_window)
        #print 'Creating plot GUI

        # Have to clear out list here instead of clear_list because clear_list() removes plot_args before this method has a chance to read
        # them and create the appropriate plot graph windows
        self.reinit_variables()

    # Clear all the elements in the list
    def clear_list(self):

        # Save plot args because they are need later in this run
        plot_args = self.plot_args
        self.reinit_variables()
        # Restore the plot args
        self.plot_args = plot_args

        self.job_list.delete(0, self.job_list.size())
        self.progress_value.set(0)
        # Update parent to refresh widget appearance
        self.parent.update()

    def on_add(self):
        single_job = JobParameters(parent=self.parent, beginning_year=1950, ending_year=2100, job_id=self.last_job_id + 1, entry=self)
        single_job.set_grid()

    def on_remove(self):
        selection = self.job_list.curselection()
        for line_number in selection:
            line_text = self.job_list.get(line_number)
            job_id = int(line_text[4:line_text.index(' ', 4)])
            job = self.job_params.pop(job_id)
            self.job_list.delete(line_number)
            print 'Removed Job ' + str(job['job_id'])
        # Fix line number
        for line_number in range(self.job_list.size()):
            line_text = self.job_list.get(line_number)
            job_id = int(line_text[4:line_text.index(' ', 4)])
            #print 'Job ' + str(job_id) + ' is now on line ' + str(line_number)
            self.job_params[job_id]['line_number'] = line_number

    def set_grid(self):
        self.grid(sticky=Tkinter.N + Tkinter.S + Tkinter.W + Tkinter.E, padx=4, pady=4)
        self.columnconfigure(0, minsize=600)
        self.rowconfigure(0, minsize=300)
        self.job_list.grid(row=0, column=0, sticky=Tkinter.N + Tkinter.S + Tkinter.E + Tkinter.W)
        self.job_list_yscroll.grid(row=0, column=1, sticky=Tkinter.N + Tkinter.S + Tkinter.W)
        self.job_list_xscroll.grid(row=1, column=0, sticky=Tkinter.E + Tkinter.W + Tkinter.N)
        self.new_job_frame.grid(row=2, column=0, pady=3, sticky=Tkinter.W)
        self.remove_job_button.grid(row=0, column=0)
        self.add_job_button.grid(row=0, column=1)
        self.progress_frame.grid(row=3, column=0, pady=3)
        self.progress_frame.columnconfigure(0, minsize=600)
        self.progress_bar.grid(row=0, column=0, sticky=Tkinter.E + Tkinter.W + Tkinter.N + Tkinter.S)
        self.button_frame.grid(row=4, column=0, sticky=Tkinter.E + Tkinter.W + Tkinter.N + Tkinter.S)
        self.button_frame.columnconfigure(0, minsize=300)
        self.button_frame.columnconfigure(1, minsize=300)
        self.process_button.pack(side=Tkinter.RIGHT)
        self.quit_button.pack(side=Tkinter.RIGHT)

    def start_jobs(self):
        # If there are no queued jobs then simply return
        if len(self.job_params) == 0 or len(self.job_list.get(0)) == 0:
            return
        # Deactivate the process button
        self.process_button.config(state = Tkinter.DISABLED)
        # Initialize the progress bar
        self.progress_value.set(0)
        # Update parent to refresh widget appearance
        self.parent.update()
        # Start process thread
        jobs_thread = JobsThread(self.job_params, self.run_job, self.on_update, self.on_resume)
        jobs_thread.start()
        self['cursor'] = 'wait'

    def on_update(self, status, line_number, step):
        if status == 'init':
            self.job_list.itemconfig(line_number, foreground='green')
            self.job_list.activate(line_number)
        elif status == 'success':
            self.job_list.itemconfig(line_number, foreground='blue')
        elif status == 'fail':
            self.job_list.itemconfig(line_number, foreground='red')
        self.progress_value.set(step)
        # Update parent to refresh widget appearance
        self.parent.update()

    def on_resume(self, job_outcomes=list()):
        self.progress_value.set(100)
        self.job_outcomes = job_outcomes
        self.event_generate('<<AskToClearJobs>>', when='tail')
        self.event_generate('<<AskToPlotGraphs>>', when='tail')
        self['cursor'] = 'arrow'

    def close_top_level_windows(self):
        #print 'Closing other top level windows'
        for top_level_window in self.top_level_windows:
            if top_level_window:
                top_level_window.withdraw()
                top_level_window.destroy()

    def notify_of_close(self, top_level_window):
        if top_level_window in self.top_level_windows:
            #print 'Removing top level window'
            self.top_level_windows.remove(top_level_window)

    def on_press(self, event):
        self.on_button = True
        self.release_pattern = "<B%d-ButtonRelease-%d>" % (event.num, event.num)
        self.parent.bind(self.release_pattern, self.on_release)

    def on_release(self, event):
        self.on_button = False

    def on_resize(self, event):
        self.parent.lift()

        if self.on_button:

            self.set_grid()

    def on_close(self):
        self.plot_args = list()
        self.withdraw()
        self.destroy()

class JobParameters(Toplevel):
    def __init__(self, parent=None, **kwargs):
        Toplevel.__init__(self, parent)
        self.title('Job Parameters')
        self.parent = parent
        self.main_frame = Frame(self)
        self.input_directory_gui = DirectorySelector(self.main_frame, 'Input Directory:')
        self.output_directory_gui = DirectorySelector(self.main_frame, 'Output Directory:', get_default=lambda: self.input_directory_gui.get_directory() + '/output/')
        self.input_directory_gui.set_notify(self.notify)
        self.beginning_year = kwargs['beginning_year'] if 'beginning_year' in kwargs else 1950
        self.ending_year = kwargs['ending_year'] if 'ending_year' in kwargs else 2100
        self.beginning_year_selector = YearSelector(self.main_frame, text="Beginning Year:", min_value=self.beginning_year, max_value=self.ending_year)
        self.ending_year_selector = YearSelector(self.main_frame, text="Ending Year:", min_value=self.beginning_year, max_value=self.ending_year)

        self.one_decade_range_var = IntVar()
        self.one_decade_range = Checkbutton(self.main_frame, text='Calculate 10 Year Range', variable=self.one_decade_range_var, command=self.on_change)
        self.two_decade_range_var = IntVar()
        self.two_decade_range = Checkbutton(self.main_frame, text='Calculate 20 Year Range', variable=self.two_decade_range_var, command=self.on_change)
        self.custom_range_var = IntVar()
        self.custom_range = Checkbutton(self.main_frame, text='Calculate Custom Year Range', variable=self.custom_range_var, command=self.on_change)
        self.custom_range_val = StringVar()
        self.custom_range_input = Spinbox(self.main_frame, from_=30, to=100, textvariable=self.custom_range_val, command=self.on_change, width=5)

        # Initialize widget values
        self.beginning_year_selector.set_value(self.beginning_year)
        self.beginning_year_selector.set_args(check_other_func=self.ending_year_selector.get_less_than)

        self.ending_year_selector.set_value(self.ending_year)
        self.ending_year_selector.set_args(check_other_func=self.beginning_year_selector.get_greater_than)

        self.one_decade_range_var.set(1)
        self.two_decade_range_var.set(1)
        self.custom_range_var.set(0)
        self.custom_range_input.config(state=Tkinter.DISABLED)

        self.button_frame = Frame(self.main_frame)
        self.ok_button = Button(self.button_frame, text='OK', command=self.on_submit)
        self.cancel_button = Button(self.button_frame, text='Cancel', command=self.on_close)
        self.job_id = kwargs['job_id'] if 'job_id' in kwargs else None
        self.entry = kwargs['entry'] if 'entry' in kwargs else None

        self.grab_set()

        self.resizable(width=False, height=False)

    def notify(self):
        self.output_directory_gui.notify()
        self.lift()

    def set_grid(self):
        # Layout child widgets
        self.main_frame.grid()

        self.input_directory_gui.set_grid(row=0, padx=6)
        self.output_directory_gui.set_grid(row=1, padx=6)

        self.beginning_year_selector.set_grid(row=2, padx=6)
        self.ending_year_selector.set_grid(row=3, padx=6)

        self.one_decade_range.grid(row=4, column=1, sticky='w', padx=6)
        self.two_decade_range.grid(row=5, column=1, sticky='w', padx=6)
        self.custom_range.grid(row=6, column=1, sticky='w', padx=6)
        self.custom_range_input.grid(row=6, column=2, sticky='w', padx=6)

        self.button_frame.grid(row=7, columnspan=3, sticky='nsew')
        self.ok_button.pack(side=Tkinter.RIGHT)
        self.cancel_button.pack(side=Tkinter.RIGHT)
        #self.ok_button.grid(row=7, column=1, pady=2)
        #self.cancel_button.grid(row=7, column=2, pady=2)

    def on_change(self):
        is_custom_range_checked = self.custom_range_var.get() == 1
        if is_custom_range_checked:
            self.custom_range_input.config(state=Tkinter.NORMAL)
        else:
            self.custom_range_input.config(state=Tkinter.DISABLED)

    def on_submit(self):
        if self.input_directory_gui.get_directory() == '' or self.output_directory_gui.get_directory() == '':
            self.on_close()
            return

        # The job parameters are extracted from the GUI here and passed to the processing thread to run the requisite job.
        job = dict()
        job['job_id'] = self.job_id
        job['delimiter'] = '.'
        job['individual_files'] = False
        job['input_directory'] = self.input_directory_gui.get_directory()
        job['output_directory'] = self.output_directory_gui.get_directory()
        job['start'] = self.beginning_year_selector.get_value()
        job['end'] = self.ending_year_selector.get_value()
        job['calculate_one_decade'] = self.one_decade_range_var.get() == 1
        job['calculate_two_decade'] = self.two_decade_range_var.get() == 1
        job['calculate_custom_range'] = self.custom_range_var.get() == 1
        job['custom_range'] = int(self.custom_range_val.get())
        job['log'] = True
        if self.entry != None:
            self.entry.add_job(job)
        self.on_close()

    def on_close(self):
        if self.parent != None:
            self.parent.focus_set()

        self.withdraw()
        self.destroy()

    def on_focus(self):
        self.focus_force()

class YearSelector():
    def __init__(self, parent=None, text='Year:', min_value=1950, max_value=2100, **kwargs):
        # NOTE: This class used to be a subclass of Frame, but it did not grid properly
        #Frame.__init__(self, parent)
        self.label = Label(parent, text=text)
        self.year = StringVar()
        self.year_selector = Spinbox(parent, from_=min_value, to=max_value, textvariable=self.year, command=self.on_change, width=5)
        self.set_args()

    def set_args(self, **kwargs):
        self.check_other_func = kwargs['check_other_func'] if 'check_other_func' in kwargs else None

    def get_value(self):
        value = int(self.year.get())
        return value

    def set_value(self, value):
        self.year.set(value)

    def set_grid(self, row=0, padx=0, pady=0):
        #self.grid(row=row)
        self.label.grid(row=row, column=0, sticky='e')
        self.year_selector.grid(row=row, column=1, padx=padx, pady=pady, sticky='w')

    def on_change(self):
        if self.check_other_func != None:
            value = int(self.year.get())
            new_value = self.check_other_func(value)
            if value != new_value:
                self.set_value(new_value)
        else:
            pass

    def get_less_than(self, compare_value):
        value = int(self.year.get())
        compare_value = int(compare_value)
        if value <= compare_value:
            return value
        return compare_value

    def get_greater_than(self, compare_value):
        value = int(self.year.get())
        compare_value = int(compare_value)
        if value >= compare_value:
            return value
        return compare_value

class DirectorySelector():
    def __init__(self, parent=None, text='Directory:', get_default=None):
        # NOTE: This class used to be a subclass of Frame, but it did not grid properly in the main window
        #Frame.__init__(self, parent)
        self.parent = parent
        self.label = Label(parent, text=text)
        self.directory = StringVar()
        on_change_cmd = parent.register(self.on_change)
        self.dir_entry = Entry(parent, textvariable=self.directory, validatecommand=on_change_cmd, validate='all')
        self.browse_btn = BrowseDirectoryButton(parent, entry=self)
        self.get_default = get_default
        self.notify_other = None

    def set_notify(self, notify_other):
        self.notify_other = notify_other

    def set_grid(self, row=0, padx=0):
        #self.grid(row=row)
        self.label.grid(row=row, column=0, sticky='e')
        self.dir_entry.grid(row=row, column=1, padx=padx, sticky='w')
        self.browse_btn.grid(row=row, column=2)

    def set_directory(self, directory):
        self.directory.set(directory)
        if self.notify_other != None:
            self.notify_other()
        #if self.parent != None:
            #self.parent.on_focus()

    def get_directory(self):
        directory = str(self.directory.get())
        if len(directory) > 0 and directory[len(directory)-1] != '/':
            directory = directory + '/'
        return directory

    def on_change(self):
        if self.get_default != None and self.get_directory() == '':
            self.set_directory(self.get_default())
        return True

    def notify(self):
        self.on_change()

class BrowseDirectoryButton(Button):
    def __init__(self, parent=None, entry=None):
        Button.__init__(self, parent, text='Browse', command=self.on_browse)
        self.parent = parent
        self.entry = entry

    def on_browse(self):
        directory = tkFileDialog.askdirectory()
        self.entry.set_directory(directory)
        #self.parent.on_focus()

class ProcessButton(Button):
    def __init__(self, parent=None, start_jobs=None, ask=False):
        Button.__init__(self, parent, text='Start', command=self.on_process)
        self.parent = parent
        self.start_jobs = start_jobs
        self.ask = ask

    def on_process(self):
        if self.ask:
            pass
        else:
            if self.start_jobs != None:
                self.start_jobs()

class QuitButton(Button):
    def __init__(self, parent=None, ask=False, top_frame=None, close_other_windows=None):
        Button.__init__(self, parent, text='Quit', command=self.on_quit)
        self.parent = parent
        self.ask = ask
        self.top_frame = top_frame
        self.close_other_windows = close_other_windows

    def on_quit(self):
        if self.ask:
            pass
        else:
            if self.close_other_windows != None:
                self.close_other_windows()
            self.winfo_toplevel().quit()

class PlotsThread(Thread):
    '''
    create_plots is the function to call to read plotting tables and generate ggplot/matplotlib plot figures
    output_files_list is the list containing the output files containing plotting data tables
    parent is the root widget to send events to when the creation has been completed
    '''

    def __init__(self, create_plots, output_files_list, parent):
        Thread.__init__(self, name='ModelRunner.PlotsThread')
        self.create_plots = create_plots
        self.output_files_list = output_files_list
        self.parent = parent

    def run(self):
        self.create_plots(self.output_files_list, log=True, gui_frame=self.parent)
        self.parent.finished_adding_plots()

class JobsThread(Thread):
    '''
    job_params is a dictionary of input arguments to pass to the program for running the job
    run_job is the function to call to start processing a job
    on_update is the function to call to update the UI when a job reates a milestone
    on_resume is the function to call when the job processing must continue
    '''

    def __init__(self, job_params, run_job=None, on_update=None, on_resume=None):
        Thread.__init__(self, name='ModelRunner.JobsThread')
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
            success = self.run_job(job)
            step += step_val
            if success:
                self.on_update('success', line_number, step)
            else:
                self.on_update('fail', line_number, step)
            job_outcomes.append(success)

        self.on_resume(job_outcomes)
