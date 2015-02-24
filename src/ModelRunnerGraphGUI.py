'''
GraphGUI.py

'''

from ttk import Frame
from ttk import Checkbutton
from ttk import Button
from ttk import PanedWindow
from ttk import Label

import tkFileDialog

import Tkinter

from Tkinter import IntVar
from Tkinter import Toplevel

from MyPmwScrolledFrame import ScrolledFrame

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import matplotlib.pyplot as plt

import ModelRunnerPlots

class GraphWindow(Toplevel):
    def __init__(self, parent=None, title=None, **kwargs):
        Toplevel.__init__(self, parent)
        if title != None:
            self.title(title)
        self.parent = parent
        self.paned_parent = PanedWindow(self)
        self.graph_frame = None
        if 'plot' in kwargs:
            if 'df' in kwargs:
                if 'plot_title' in kwargs:
                    if 'y_label' in kwargs:
                        self.graph_frame = GraphFrame(self, self.paned_parent, plot=kwargs['plot'], df=kwargs['df'], plot_title=kwargs['plot_title'], y_label=kwargs['y_label'], log_filename=kwargs['log_filename'])
                    else:
                        self.graph_frame = GraphFrame(self, self.paned_parent, plot=kwargs['plot'], df=kwargs['df'], plot_title=kwargs['plot_title'], log_filename=kwargs['log_filename'])
                else:
                    self.graph_frame = GraphFrame(self, self.paned_parent, plot=kwargs['plot'], df=kwargs['df'], log_filename=kwargs['log_filename'])

        self.protocol('WM_DELETE_WINDOW', self.on_close)

        # NOTE: Keep the window from being resized because child widgets don't seem to fit properly
        #self.resizable(width=False, height=False)
        self.bind('<Configure>', self.on_resize)

    def set_grid(self):
        #self.grid()
        self.paned_parent.pack(expand=True, fill=Tkinter.BOTH)
        if self.graph_frame != None:
            self.graph_frame.set_grid()

    def unset_grid(self):
        #self.grid_forget()
        self.paned_parent.pack_forget()
        if self.graph_frame != None:
            self.graph_frame.unset_grid()

    def on_close(self):
        self.parent.notify_of_close(self)
        self.withdraw()
        self.destroy()

    def on_resize(self, event):
        #print 'In on_resize'
        if isinstance(event.widget, Toplevel):
            #print 'Resizing window'
            self.unset_grid()
            self.set_grid()
            self.update()

class GraphFrame(Frame):
    def __init__(self, parent, paned_window, **kwargs):
        Frame.__init__(self, paned_window)
        self.parent = parent

        self.df_column_frame = ScrolledFrame(self, vertflex='expand')

        self.graph_frame = ScrolledFrame(self, horizflex='expand', vertflex='expand')
        self.plot_figure = kwargs['plot'] if 'plot' in kwargs else None

        self.plot_title = kwargs['plot_title'] if 'plot_title' in kwargs else 'Line Plot'
        self.y_label = kwargs['y_label'] if 'y_label' in kwargs else 'y'
        self.df = kwargs['df'] if 'df' in kwargs else DataFrame() # If the dataframe wasn't passed in, then create an empty dataframe

        plot_selected_avg = ModelRunnerPlots.get_avg_plot(self.plot_title, self.y_label, self.df, None)
        self.plot_figure = plot_selected_avg
        self.graph_canvas = FigureCanvasTkAgg(plot_selected_avg, master=self.graph_frame.interior())

        self.col_list = list()

        for col in self.df.columns:
            if col != 'year' and 'Average' not in col:
                col_var = IntVar()
                col_var.set(0)
                col_checkbox = Checkbutton(self.df_column_frame.interior(), text=col, variable=col_var, command=self.on_col_check)
                self.col_list.append([col_var, col_checkbox, col])

        avg_dataframe, dataframe = ModelRunnerPlots.find_avg_dataframe(self.df)
        for col in avg_dataframe.columns:
            if col != 'year':
                col_var = IntVar()
                col_var.set(0)
                col_checkbox = Checkbutton(self.df_column_frame.interior(), text=col, variable=col_var, command=self.on_col_check)
                self.col_list.append([col_var, col_checkbox, col])

        self.log_filename_frame = Frame(self)
        self.log_label = Label(self.log_filename_frame, text='Logfile: ' + kwargs['log_filename']) if 'log_filename' in kwargs else None

        self.button_frame = Frame(self)
        self.close_button = Button(self.button_frame, text='Close', command=self.on_close)
        self.save_button = Button(self.button_frame, text='Save', command=self.on_save)

    def set_grid(self):
        #print 'Resizing graph frame'
        #self.grid(padx=4, pady=4)
        self.pack(padx=4, pady=4, expand=True, fill=Tkinter.BOTH)
        #self.rowconfigure(0, minsize=600)
        #self.columnconfigure(0, minsize=100)
        #self.columnconfigure(1, minsize=600)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=5)
        self.rowconfigure(0, weight=1)

        self.df_column_frame.grid(row=0, column=0, sticky=Tkinter.N + Tkinter.S + Tkinter.E + Tkinter.W)
        #self.df_column_frame.pack(side=Tkinter.LEFT, expand=True, fill=Tkinter.BOTH)
        row_index = 0
        for col in self.col_list:
            checkButton = col[1]
            checkButton.grid(sticky=Tkinter.E + Tkinter.W)
            row_index += 1

        self.graph_frame.grid(row=0, column=1, sticky=Tkinter.N + Tkinter.S + Tkinter.E + Tkinter.W)
        #self.graph_frame.pack(side=Tkinter.RIGHT, expand=True, fill=Tkinter.BOTH)
        try:
            self.graph_canvas.get_tk_widget().grid(row=0, column=0, sticky=Tkinter.N + Tkinter.S + Tkinter.E + Tkinter.W)
            #self.graph_canvas.get_tk_widget().pack(expand=True, fill=Tkinter.BOTH)
	except AttributeError:
		pass
        self.log_filename_frame.grid(row=1, column=0, sticky=Tkinter.N + Tkinter.S + Tkinter.E + Tkinter.W)
        if self.log_label != None:
            self.log_label.pack(side=Tkinter.LEFT)

        self.button_frame.grid(row=1, column=1, sticky=Tkinter.N + Tkinter.S + Tkinter.E + Tkinter.W)
        #self.button_frame.pack(side=Tkinter.BOTTOM, expand=True, fill=Tkinter.X)
        self.close_button.pack(side=Tkinter.RIGHT)
        self.save_button.pack(side=Tkinter.RIGHT)

    def unset_grid(self):
        self.pack_forget()
        self.df_column_frame.grid_forget()
        self.graph_frame.grid_forget()
	try:
        	self.graph_canvas.get_tk_widget().grid_forget()
	except AttributeError:
		pass
        self.log_filename_frame.grid_forget()
        if self.log_label != None:
            self.log_label.pack_forget()
        self.button_frame.grid_forget()
        self.close_button.pack_forget()
        self.save_button.pack_forget()

    def on_col_check(self):
        # Based upon what is checked, a new plot should be created
        value_vars = list()

        for col in self.col_list:
            if col[0].get() == 1:
                #print col[2] + ' is checked'
                value_vars.append(col[2])
            else:
                pass
                #print col[2] + ' is not checked'

        plot_selected = ModelRunnerPlots.create_line_plot(self.plot_title, self.y_label, self.df, None, value_vars=value_vars)
        #if len(value_vars) == 0:
            #plot_selected = ModelRunnerPlots.get_avg_plot(self.plot_title, self.y_label, self.df, None)
        plt.close(self.plot_figure)
	try:
        	self.graph_canvas.get_tk_widget().grid_remove()
		self.graph_canvas = FigureCanvasTkAgg(plot_selected, master=self.graph_frame.interior())
        	self.graph_canvas.get_tk_widget().grid(row=0, column=1, sticky=Tkinter.N + Tkinter.S + Tkinter.E + Tkinter.W)
	except AttributeError:
		pass
        
        self.plot_figure = plot_selected

    def on_close(self):
        if self.parent != None:
            self.parent.on_close()

    def on_save(self):
        if self.plot_figure != None:
            filename = tkFileDialog.asksaveasfilename()
            if filename != None and len(filename) > 0:
                dotIndex = filename.rindex('.')
                # Enforce the 'png' file extension
                filename = filename[0:dotIndex+1] + 'png'
                self.plot_figure.savefig(filename, format='png')
