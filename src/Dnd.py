"""Drag-and-drop support for Tkinter.

This is very preliminary.  I currently only support dnd *within* one
application, between different windows (or within the same window).

I an trying to make this as generic as possible -- not dependent on
the use of a particular widget or icon type, etc.  I also hope that
this will work with Pmw.

To enable an object to be dragged, you must create an event binding
for it that starts the drag-and-drop process. Typically, you should
bind <ButtonPress> to a callback function that you write. The function
should call Tkdnd.dnd_start(source, event), where 'source' is the
object to be dragged, and 'event' is the event that invoked the call
(the argument to your callback function).  Even though this is a class
instantiation, the returned instance should not be stored -- it will
be kept alive automatically for the duration of the drag-and-drop.

When a drag-and-drop is already in process for the Tk interpreter, the
call is *ignored*; this normally averts starting multiple simultaneous
dnd processes, e.g. because different button callbacks all
dnd_start().

The object is *not* necessarily a widget -- it can be any
application-specific object that is meaningful to potential
drag-and-drop targets.

Potential drag-and-drop targets are discovered as follows.  Whenever
the mouse moves, and at the start and end of a drag-and-drop move, the
Tk widget directly under the mouse is inspected.  This is the target
widget (not to be confused with the target object, yet to be
determined).  If there is no target widget, there is no dnd target
object.  If there is a target widget, and it has an attribute
dnd_accept, this should be a function (or any callable object).  The
function is called as dnd_accept(source, event), where 'source' is the
object being dragged (the object passed to dnd_start() above), and
'event' is the most recent event object (generally a <Motion> event;
it can also be <ButtonPress> or <ButtonRelease>).  If the dnd_accept()
function returns something other than None, this is the new dnd target
object.  If dnd_accept() returns None, or if the target widget has no
dnd_accept attribute, the target widget's parent is considered as the
target widget, and the search for a target object is repeated from
there.  If necessary, the search is repeated all the way up to the
root widget.  If none of the target widgets can produce a target
object, there is no target object (the target object is None).

The target object thus produced, if any, is called the new target
object.  It is compared with the old target object (or None, if there
was no old target widget).  There are several cases ('source' is the
source object, and 'event' is the most recent event object):

- Both the old and new target objects are None.  Nothing happens.

- The old and new target objects are the same object.  Its method
dnd_motion(source, event) is called.

- The old target object was None, and the new target object is not
None.  The new target object's method dnd_enter(source, event) is
called.

- The new target object is None, and the old target object is not
None.  The old target object's method dnd_leave(source, event) is
called.

- The old and new target objects differ and neither is None.  The old
target object's method dnd_leave(source, event), and then the new
target object's method dnd_enter(source, event) is called.

Once this is done, the new target object replaces the old one, and the
Tk mainloop proceeds.  The return value of the methods mentioned above
is ignored; if they raise an exception, the normal exception handling
mechanisms take over.

The drag-and-drop processes can end in two ways: a final target object
is selected, or no final target object is selected.  When a final
target object is selected, it will always have been notified of the
potential drop by a call to its dnd_enter() method, as described
above, and possibly one or more calls to its dnd_motion() method; its
dnd_leave() method has not been called since the last call to
dnd_enter().  The target is notified of the drop by a call to its
method dnd_commit(source, event).

If no final target object is selected, and there was an old target
object, its dnd_leave(source, event) method is called to complete the
dnd sequence.

Finally, the source object is notified that the drag-and-drop process
is over, by a call to source.dnd_end(target, event), specifying either
the selected target object, or None if no target object was selected.
The source object can use this to implement the commit action; this is
sometimes simpler than to do it in the target's dnd_commit().  The
target's dnd_commit() method could then simply be aliased to
dnd_leave().

At any time during a dnd sequence, the application can cancel the
sequence by calling the cancel() method on the object returned by
dnd_start().  This will call dnd_leave() if a target is currently
active; it will never call dnd_commit().

"""

import sys

import Tkinter
import ttk
import MyPmwScrolledFrame

from PIL import Image
from PIL import ImageTk

class DrawCanvas(Tkinter.Toplevel):
    def __init__(self, root, geometry, parent, alpha=0.50):
        Tkinter.Toplevel.__init__(self)
        #geometry = geometry[geometry.find('+'):]
        #print 'Geometry ' + geometry
        #x1, y1, x2, y2 = root.bbox()
        #print 'X ' + str(root.winfo_rootx())
        #print 'Y ' + str(root.winfo_rooty())
        geometry = geometry[0:geometry.rindex('+')] + '+' + str(root.winfo_rooty())
        self.geometry(geometry)
        self.overrideredirect(1)
        self.transient(root)
        self.attributes('-alpha', alpha)
        self.canvas = Tkinter.Canvas(self)
        self.canvas.pack(expand=True, fill=Tkinter.BOTH)
        self.canvas.name = 'Draw Canvas'
        self.parent = parent
        self.dnd_accept = parent.dnd_accept

# The factory function

def dnd_start(source, event, parent):
    h = DndHandler(source, event, parent)
    #print 'Created new DnD Handler'
    if h.root:
        return h
    else:
        return None


# The class that does the work

class DndHandler:

    root = None

    def __init__(self, source, event, parent):
        if event.num > 5:
            return
        root = event.widget._root()
        try:
            root.__dnd
            return # Don't start recursive dnd
        except AttributeError:
            root.__dnd = self
            self.root = root
        self.source = source
        self.target = None
        self.initial_button = button = event.num
        self.initial_widget = widget = event.widget
        self.source_widget = source.parent.scrolled_frame
        self.release_pattern = "<B%d-ButtonRelease-%d>" % (button, button)
        self.save_cursor = widget['cursor'] or ""
        widget.dnd_bind(self.release_pattern, self.on_release, self.on_motion, "hand2")

        self.parent = parent
        #self.draw_canvas = DrawCanvas(self.root.winfo_toplevel(), self.root.winfo_toplevel().winfo_geometry(), parent)
        self.draw_canvas = DrawCanvas(self.parent.root, self.parent.root.winfo_geometry(), self.parent)

    def __del__(self):
        root = self.root
        self.root = None
        if root:
            try:
                del root.__dnd
            except AttributeError:
                pass

    def on_motion(self, event):
        #print 'On motion'
        x, y = event.x_root, event.y_root
        target_widget = self.source_widget.winfo_containing(x, y)
        source = self.source


    def on_motion(self, event):
        #print 'On motion'
        x, y = event.x_root, event.y_root
        #target_widget = self.initial_widget.winfo_containing(x, y)
        #self.parent.dnd_lift()
        #target_widget = self.source_widget.winfo_containing(x, y)
        source = self.source
        target_widget = self.parent.dnd_lift(x, y)
        if target_widget == None:
            self.parent.dnd_enter(source, event, self.draw_canvas.canvas, self.draw_canvas)
            self.target = self.parent
            return
        #print 'Target widget class: ' + target_widget.winfo_class()
        new_target = None
        while target_widget:
            try:
                attr = target_widget.dnd_accept
            except AttributeError:
                pass
            else:
                new_target = attr(source, event)
            target_widget = target_widget.master
        old_target = self.target
        if old_target:
            pass #print 'Old Target: ' + old_target.name
        if new_target:
            pass #print 'New target: ' + new_target.name
        if old_target is new_target:
            if old_target:
                old_target.dnd_motion(source, event, self.draw_canvas.canvas)
        else:
            if old_target:
                #print 'On Leave'
                self.target = None
                old_target.dnd_leave(source, event, self.draw_canvas.canvas)
                source.moved = True
            if new_target:
                #print 'On Enter'
                new_target.dnd_enter(source, event, self.draw_canvas.canvas, self.draw_canvas)
                self.target = new_target
        #print 'Finished On motion\n'

    def on_release(self, event):
        self.finish(event, 1)

    def cancel(self, event=None):
        self.finish(event, 0)

    def finish(self, event, commit=0):
        x, y = event.x, event.y
        target = self.target
        source = self.source
        widget = self.initial_widget
        root = self.root
        try:
            del root.__dnd
            self.initial_widget.unbind(self.release_pattern)
            self.initial_widget.unbind("<Motion>")
            widget['cursor'] = self.save_cursor
            self.target = self.source = self.initial_widget = self.root = None
            if target:
                if commit:
                    target.dnd_commit(source, event, self.draw_canvas.canvas)
                else:
                    target.dnd_leave(source, event, self.draw_canvas.canvas)
        finally:
            source.dnd_end(target, event)
            self.draw_canvas.canvas.delete(source.id)
            self.draw_canvas.destroy()

class IconLabel(ttk.Frame):

    def __init__(self, parent, text, borderwidth, relief, icon_fname, root):

        ttk.Frame.__init__(self, parent, borderwidth=borderwidth, relief=relief)
        self.label_text = Tkinter.StringVar(value=text)
        #max_word_length = self.longest_word_length(text)
        # If the length of the text is greater than twice then truncate it
        if len(text) > 12:
            text = text[0:12] + '...'

        self.label = ttk.Label(self, text=text, wraplength=60)
        image = Image.open(icon_fname)
        #icon = ImageTk.PhotoImage(image=image, master=root)
        icon = ImageTk.PhotoImage(image=image)
        #print 'Icon is: ' + icon_fname
        self.button = ttk.Button(master=self, image=icon)
        self.image = icon
        self.button.config(state=Tkinter.DISABLED)
        self.release_pattern = None
        self.btn_press_pattern = None

        self.hint_text = self.label_text
        self.label.hint_text = self.hint_text
        self.button.hint_text = self.hint_text

    def longest_word_length(self, text):
        words = text.split(' ')
        max_length = 0
        for word in words:
            if len(word) > max_length:
                max_length = word
        return max_length

    def set_grid(self, row, column):
        self.grid(row=row, column=column, padx=2, pady=2)
        self.button.grid(row=0)
        self.label.grid(row=1)

    def unset_grid(self):
        self.button.grid_forget()
        self.label.grid_forget()
        self.grid_forget()

    def btn_press_bind(self, btn_press_pattern, on_press):
        self.bind(btn_press_pattern, on_press)
        #self.label.bind(btn_press_pattern, on_press)
        #self.button.bind(btn_press_pattern, on_press)
        self.label.bind(btn_press_pattern, self.gen_on_btn_press)
        self.button.bind(btn_press_pattern, self.gen_on_btn_press)
        self.btn_press_pattern = btn_press_pattern

    def dnd_bind(self, release_pattern, on_release, on_motion, cursor_icon):
        #print release_pattern
        self.bind(release_pattern, on_release)
        self.bind("<Motion>", on_motion)
        self.label.bind(release_pattern, self.gen_on_release)
        self.label.bind("<Motion>", self.gen_on_motion)
        self.button.bind(release_pattern, self.gen_on_release)
        self.button.bind("<Motion>", self.gen_on_motion)
        self['cursor'] = cursor_icon
        self.release_pattern = release_pattern

    def gen_on_btn_press(self, event):
        #print 'gen on btn press'
        self.event_generate(self.btn_press_pattern, button=event.num, when='tail')

    def gen_on_release(self, event):
        #print 'gen on release'
        self.event_generate(self.release_pattern, when='tail')

    def gen_on_motion(self, event):
        #print 'gen on motion'
        self.event_generate("<Motion>", x=event.x, y=event.y, when='tail')

    def create_window(self, canvas, x, y):
        #print 'Create window'
        self.button.grid(row=0)
        self.label.grid(row=1)
        id = canvas.create_window(x, y, window=self)
        return id

    def get_label_text(self):
        return self.label_text.get()

# ----------------------------------------------------------------------
# The rest is here for testing and demonstration purposes only!

class InteractiveFile:

    def __init__(self, name, icon_fname, root=None):
        self.name = name
        self.icon_fname = icon_fname
        #self.canvas = self.label = self.id = self.parent = None
        self.scrolled_frame = self.label = self.id = self.parent = None
        self.moved = False
        self.root = root

    def attach(self, parent, x=10, y=10, grid_all=False):

        if parent.scrolled_frame is self.scrolled_frame:
            #self.canvas.coords(self.id, x, y)
            return
        if self.scrolled_frame:
            self.detach()
        if not parent.scrolled_frame:
            return
        label = IconLabel(parent.scrolled_frame.interior(), text=self.name,
                          borderwidth=2, relief='flat', icon_fname=self.icon_fname, root=self.root)
        id = None

        #label.grid(row=self.row, column=self.column)
        self.scrolled_frame = parent.scrolled_frame
        #self.canvas = parent.canvas
        self.label = label
        self.id = id
        self.parent = parent
        label.btn_press_bind("<ButtonPress>", self.press)

        parent.attach(window=label)

    def detach(self):
        self.parent.detach(self.label)

        #canvas = self.canvas
        #if not canvas:
            #return
        scrolled_frame = self.scrolled_frame
        if not scrolled_frame:
            return
        id = self.id
        label = self.label
        #self.canvas = self.label = self.id = self.scrolled_frame = None
        self.label = self.id = self.scrolled_frame = self.parent = None
        #canvas.delete(id)
        label.destroy()

    def press(self, event):
        h = dnd_start(self, event, self.parent)
        if h:
            # where the pointer is relative to the label widget:
            self.x_off = event.x
            self.y_off = event.y
            # where the widget is relative to the canvas:
            #self.x_orig, self.y_orig = self.canvas.coords(self.id)
            self.x_orig, self.y_orig = self.label.winfo_rootx(), self.label.winfo_rooty()

    def move(self, event, canvas):
        x, y = self.where(canvas, event)
        canvas.coords(self.id, x, y)

    def putback(self, canvas):
        canvas.coords(self.id, self.x_orig, self.y_orig)

    def where(self, canvas, event):
        # where the corner of the canvas is relative to the screen:
        x_org = canvas.winfo_rootx()
        y_org = canvas.winfo_rooty()
        # where the pointer is relative to the canvas widget:
        x = event.x_root - x_org
        y = event.y_root - y_org
        # compensate for initial pointer offset
        return x - self.x_off, y - self.y_off

    def dnd_end(self, target, event):
        pass

class DnDFilePane:

    def __init__(self, root, pane_name):
        #self.top = Tkinter.Toplevel(root)
        self.top = ttk.LabelFrame(root, borderwidth=1, text=pane_name, relief='sunken')
        self.name = pane_name
        #self.top.dnd_accept = self.dnd_accept
        #self.canvas_xscroll = ttk.Scrollbar(self.top, orient=Tkinter.HORIZONTAL)
        #self.canvas_yscroll = ttk.Scrollbar(self.top, orient=Tkinter.VERTICAL)
        self.scrolled_frame = MyPmwScrolledFrame.ScrolledFrame(self.top, horizflex='expand', vertflex='expand')
        self.scrolled_frame.interior().config(borderwidth=1, relief='sunken')

        #self.canvas = Tkinter.Canvas(self.scrolled_frame.interior())

        #self.canvas.config(xscrollcommand=self.canvas_xscroll.set, yscrollcommand=self.canvas_yscroll.set)

        #self.canvas_xscroll.config(command=self.canvas.xview)
        #self.canvas_yscroll.config(command=self.canvas.yview)

        #self.id = self.canvas.create_window(10, 10, window=self.top)
        #self.canvas.pack(fill="both", expand=1)
        #self.canvas.dnd_accept = self.dnd_accept
        self.scrolled_frame.master = None
        self.scrolled_frame.interior().root = self
        self.scrolled_frame.component('hull').root = self
        self.scrolled_frame.dnd_accept = self.dnd_accept
        self.scrolled_frame.component('hull').dnd_accept = self.dnd_accept
        self.scrolled_frame.interior().dnd_accept = self.dnd_accept

        self.row = -1
        self.column = -1
        self.padx = -1
        self.pady = -1
        self.sticky = None

        self.root = root

        self.moved = False

        self.children = list()

        self.current_width = 0

    def dnd_lift(self, x, y):
        parent = self.root.winfo_toplevel()
        #print '\n'
        #print 'Parent: ' + parent.winfo_class()

        find = self.dnd_find(parent, x, y)
        if not find:
            pass
            #print 'Target not found'
        else:
            pass
            #print 'Target found: ' + find.winfo_class()
        #print '\n'
        return find

    def dnd_find(self, target_candidate, x, y):
        #print 'Target: ' + target_candidate.winfo_class()

        if target_candidate.winfo_class() != 'ScrolledFrame':
            children = target_candidate.winfo_children()
            for child in children:
                #print 'Calling find'
                find = self.dnd_find(child, x, y)
                #print 'Return from find'
                if find:
                    return find

        # If the target_candidate is of the same type as the target type
        # then determine if it is the actual target

        try:
            x1, y1, x2, y2 = target_candidate.bbox()
        except Tkinter.TclError as tcle:
            #print 'TclError: ' + str(tcle)
            return None
        #x += target_candidate.winfo_rootx()
        x1 += target_candidate.winfo_rootx()
        x2 += target_candidate.winfo_rootx()
        #y += target_candidate.winfo_rooty()
        y1 += target_candidate.winfo_rooty()
        y2 += target_candidate.winfo_rooty()
        #print 'x1 = ' + str(x1) + ' x2 = ' + str(x2) + ' y1 = ' + str(y1) + ' y2 = '  + str(y2)
        #print 'x = ' + str(x) + ' y = ' + str(y)
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return target_candidate

        return None

    def dnd_accept(self, source, event):
        return self

    def dnd_enter(self, source, event, canvas, root):
        #print 'Dnd Enter'

        #canvas.focus_set() # Show highlight border
        source.scrolled_frame.interior().focus_set()
        x, y = source.where(canvas, event)
        if source.id == None:
            label = IconLabel(canvas, text=source.name,
                          borderwidth=2, relief='raised',
                          icon_fname=source.icon_fname, root=root)
            #id = canvas.create_window(x, y, window=label)
            id = label.create_window(canvas, x, y)
            source.id = id
        x1, y1, x2, y2 = canvas.bbox(source.id)
        dx, dy = x2-x1, y2-y1
        #print 'dx ' + str(dx)
        #print 'dy ' + str(dy)
        #self.dndid = canvas.create_rectangle(x, y, x+dx, y+dy)
        self.dnd_motion(source, event, canvas)

    def dnd_motion(self, source, event, canvas):
        #print 'Dnd motion'

        x, y = source.where(canvas, event)
        #x1, y1, x2, y2 = canvas.bbox(self.dndid)
        #print source.id
        x1, y1, x2, y2 = canvas.bbox(source.id)
        #canvas.move(self.dndid, x-x1, y-y1)

        if source.moved:
            x_center = source.label.winfo_width()
            y_center = source.label.winfo_height()
            x1 -= int(float(x_center)/2.0)
            y1 -= int(float(y_center)/2.0)
            source.moved = False

        canvas.move(source.id, x-x1, y-y1)

    def dnd_leave(self, source, event, canvas):
        #print 'Dnd leave'

        self.top.focus_set() # Hide highlight border
        canvas.delete(source.id)
        source.id = None

    def dnd_commit(self, source, event, canvas):
        #print 'Dnd commit'

        self.dnd_leave(source, event, canvas)
        x, y = source.where(canvas, event)
        source.attach(self, x, y, True)

    def set_grid(self, row, column, sticky, padx, pady):

        self.row = row
        self.column = column
        self.sticky = sticky
        self.padx = padx
        self.pady = pady

        self.regrid()

    def attach(self, window):
        self.children.append(window)

        self.regrid()

    def detach(self, window):

        #window.grid_forget()
        window.unset_grid()

        self.children.remove(window)

        self.regrid()

    def regrid(self):

        if self.row == 0:
            self.top.pack(expand=True, fill=Tkinter.BOTH, side=Tkinter.LEFT)
        else:
            self.top.pack(expand=True, fill=Tkinter.BOTH, side=Tkinter.RIGHT)
        #self.scrolled_frame.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0)
        self.scrolled_frame.pack(expand=True, fill=Tkinter.BOTH)

        # Re-grid children
        children = self.children
        current_row = 0
        current_column = 0
        self.current_width = 0
        for child in children:
            child.set_grid(row=current_row, column=current_column)
            current_column += 1

            window_width = self.scrolled_frame.component('hull').winfo_width()
            child_width = child.winfo_width()
            #print 'Child width=' + str(child_width) + ', Interior width=' + str(window_width)
            #print self.scrolled_frame.components()
            self.current_width += child_width
            if self.current_width > window_width:
                current_column = 0
                current_row += 1
                self.current_width = 0

        self.refresh()

    def ungrid(self):
        children = self.children
        for child in children:
            child.label.grid_forget()
            child.grid_forget()
        self.scrolled_frame.pack_forget()
        self.top.pack_forget()

    def resize(self, width, height):
        self.top.grid_remove()

        self.regrid()

    def update_dims(self):
        self.width = self.top.winfo_width()
        self.height = self.top.winfo_height()

    def refresh(self):
        #self.scrolled_frame.component('hull').update()
        self.scrolled_frame.component('horizscrollbar').propagate()
        self.scrolled_frame.component('vertscrollbar').propagate()

    def get_children_labels(self):
        children_labels = list()
        for child in self.children:
            children_labels.append(child.get_label_text())

        return children_labels

    def clear(self):
        self.ungrid()
        self.children = list()


class MainContainer:
    def __init__(self, main, left_frame, right_frame, finish_creating_plot_gui):
        self.main = main
        self.left_frame = left_frame
        self.right_frame = right_frame
        self.width = main.winfo_width()
        self.height = main.winfo_height()
        self.release_pattern = None
        self.on_button = False
        self.finish_creating_plot_gui = finish_creating_plot_gui

        self.hint_label = None
        #self.main.bind('<Motion>', self.on_label_hint)

        #self.draw_canvas = DrawCanvas(self.main, self.main.winfo_geometry(), self, alpha=0.0)

    def on_resize(self, event):

        width = event.width
        height = event.height

        if isinstance(event.widget, Tkinter.Tk):
            #print 'Event resize: ' + event.widget.winfo_class() + ' ' + str(event.num)

            self.left_frame.regrid()

            self.right_frame.regrid()

    def on_press(self, event):
        self.on_button = True
        self.release_pattern = "<B%d-ButtonRelease-%d>" % (event.num, event.num)
        self.main.bind(self.release_pattern, self.on_release)

    def on_release(self, event):
        self.on_button = False

    def clear_windows(self):
        self.main.withdraw()
        self.left_frame.ungrid()
        self.right_frame.ungrid()

    def on_continue(self):
        self.clear_windows()

        # TODO: Iterate through all the items in RIGHT pane to get the plots the user wants and then pass them
        # back to the caller
        self.finish_creating_plot_gui(self.right_frame.get_children_labels())

    def on_close(self):
        self.clear_windows()

        self.finish_creating_plot_gui(list())

    def on_label_hint(self, event):
        x, y = event.x_root, event.y_root
        target_widget = self.dnd_lift(x, y)

        if isinstance(target_widget, ttk.Label):
            print 'The underlying widget is a ttk.Label'
        elif isinstance(target_widget, ttk.Button):
            print 'The underlying widget is a ttk.Button'
        elif isinstance(target_widget, ttk.LabelFrame):
            print 'The underlying widget is a ttk.LabelFrame'
        elif isinstance(target_widget, ttk.Frame):
            print 'The underlying widget is a ttk.Frame'
        else:
            print 'The underlying widget is of an unknown widget type'

        label_text = 'Graph file'
        try:
            label_text = target_widget.hint_text

        except AttributeError:
            print 'Could not find hint label'
        if self.hint_label != None:
            label = self.hint_label
            label.destroy()
            self.hint_label = None

        self.hint_label = ttk.Label(target_widget, text=label_text)

        self.id = self.draw_canvas.canvas.create_window(x, y, window=self.hint_label)
        print 'Created hint text'

    def dnd_lift(self, x, y):
        parent = self.main.winfo_toplevel()
        #print '\n'
        #print 'Parent: ' + parent.winfo_class()

        find = self.dnd_find(parent, x, y)
        if not find:
            pass
            #print 'Target not found'
        else:
            pass
            #print 'Target found: ' + find.winfo_class()
        #print '\n'
        return find

    def dnd_find(self, target_candidate, x, y):
        #print 'Target: ' + target_candidate.winfo_class()

        if target_candidate.winfo_class() != 'TopLevel':
            children = target_candidate.winfo_children()
            for child in children:
                #print 'Calling find'
                find = self.dnd_find(child, x, y)
                #print 'Return from find'
                if find:
                    return find

        # If the target_candidate is of the same type as the target type
        # then determine if it is the actual target

        try:
            x1, y1, x2, y2 = target_candidate.bbox()
        except Tkinter.TclError as tcle:
            #print 'TclError: ' + str(tcle)
            return None
        #x += target_candidate.winfo_rootx()
        x1 += target_candidate.winfo_rootx()
        x2 += target_candidate.winfo_rootx()
        #y += target_candidate.winfo_rooty()
        y1 += target_candidate.winfo_rooty()
        y2 += target_candidate.winfo_rooty()
        #print 'x1 = ' + str(x1) + ' x2 = ' + str(x2) + ' y1 = ' + str(y1) + ' y2 = '  + str(y2)
        #print 'x = ' + str(x) + ' y = ' + str(y)
        if x >= x1 and x <= x2 and y >= y1 and y <= y2:
            return target_candidate

        return None

    def dnd_accept(self):
        pass

def printChildren(parent, depth=0):
    #print 'Widget ' + parent.winfo_class() + ' width = ' + str(parent.winfo_width()) + ' height = ' + str(parent.winfo_height())
    if depth < 100:
        children = parent.winfo_children()
        for child in children:
            printChildren(child, depth)

def createFrame(parent=None, plot_title=None, graphs=list(), finish_creating_plot_gui=None):
    main = parent
    if main == None:
        main = Tkinter.Tk()

    else:
        main = Tkinter.Toplevel(parent)

    if plot_title == None:
        main.title('Graphs')
    else:
        main.title(plot_title)

    btn_frame_outer = ttk.Frame(main)
    btn_frame_outer.pack(expand=True, fill=Tkinter.X, side=Tkinter.BOTTOM)
    btn_frame_inner = ttk.Frame(btn_frame_outer)
    btn_frame_inner.pack(side=Tkinter.RIGHT)

    left_frame = DnDFilePane(main, pane_name='Output Graphs')
    left_frame.set_grid(row=0, column=0, sticky=Tkinter.E + Tkinter.W + Tkinter.N + Tkinter.S, padx=2, pady=2)

    right_frame = DnDFilePane(main, pane_name='Graphs To Display')
    right_frame.set_grid(row=0, column=1, sticky=Tkinter.E + Tkinter.W + Tkinter.N + Tkinter.S, padx=2, pady=2)

    filename = 'file_icon.png'

    for graph in graphs:
        interactive_file = InteractiveFile(name=graph, icon_fname=filename, root=main)
        interactive_file.attach(left_frame)

    left_frame_children = left_frame.scrolled_frame.interior().winfo_children()
    child_index = 0
    for child in left_frame_children:
        #print 'Child ' + str(child_index) + ' width: ' + str(child.winfo_reqwidth())
        #print 'Child ' + str(child_index) + ' height: ' + str(child.winfo_reqheight())
        child_index += 1

    #main.minsize(width=10, height=10)
    #main.maxsize(width=100, height=100)

    main_container = MainContainer(left_frame=left_frame, right_frame=right_frame, main=main, finish_creating_plot_gui=finish_creating_plot_gui)

    main.bind('<ButtonPress>', main_container.on_press)
    main.bind('<Configure>', main_container.on_resize)

    ok_btn = ttk.Button(btn_frame_inner, text='OK', command=main_container.on_continue)
    cancel_btn = ttk.Button(btn_frame_inner, text='Cancel', command=main_container.on_close)

    cancel_btn.grid(row=1, column=0, sticky=Tkinter.E + Tkinter.W + Tkinter.N + Tkinter.S, padx=2, pady=2)
    ok_btn.grid(row=1, column=1, sticky=Tkinter.E + Tkinter.W + Tkinter.N + Tkinter.S, padx=2, pady=2)

    main.grid()

    return main

def main(argv):

    #printChildren(main)

    #sample_args = list()
    #for i in range(20):
        #sample_args.append('File ' + str(i))

    #main = createFrame(None, sample_args)

    #main.mainloop()

    main = Tkinter.Tk()

    sample_args = list()
    for i in range(20):
        sample_args.append('File ' + str(i))

    main.grid()

    main_frame = createFrame(parent=main, graphs=sample_args)

    main.mainloop()

if __name__ == '__main__':
    main(sys.argv)