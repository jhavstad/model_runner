#! /usr/bin/env python

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QApplication, QGroupBox, QSplitter, QSizePolicy, QPushButton, QToolTip
from PyQt5.QtGui import QMouseEvent, QDrag, QImage, QPixmap
from PyQt5.QtCore import QMimeData, QVariant, pyqtSignal, QSize, QEvent, QPoint
from PyQt5.Qt import Qt

import sys

import PyQtExtras

class DndPlotFile(QFrame):
    def __init__(self, text):
        QLabel.__init__(self)

        self.text = text

        self.layout = QVBoxLayout(self)

        self.image_label = QLabel()
        image = QImage('file_icon.png')
        self.image_label.setPixmap(QPixmap.fromImage(image))
        self.image_label.setAlignment(Qt.AlignCenter)

        # Truncate the filename if it is too long (but its fullname and path are saved in an instance variable)
        last_path_seperator_index = text.rfind('/')
        text = text[last_path_seperator_index+1:]

        if len(text) > 12:
            text = text[0:12] + '...'
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.text_label)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

    def get_text(self):
        return self.text

    def event(self, e):
        if e.type() == QEvent.Enter:
            self.show_tool_tip(e)
            return True
        elif e.type() == QEvent.Leave:
            self.hide_tool_tip(e)
            return True
        return QFrame.event(self, e)

    def show_tool_tip(self, e):
        sum_pos = self.pos()

        parent = self.parent()
        sum_pos += parent.pos()

        grand_parent = parent.parent()
        sum_pos += grand_parent.pos()

        great_grand_parent = grand_parent.parent()
        sum_pos += great_grand_parent.pos()

        great_great_grand_parent = great_grand_parent.parent()
        sum_pos += great_great_grand_parent.pos()

        great_great_great_grand_parent = great_great_grand_parent.parent()
        sum_pos += great_great_great_grand_parent.pos()

        great_great_great_great_grand_parent = great_great_great_grand_parent.parent()
        sum_pos += great_great_great_great_grand_parent.pos()

        sum_pos += QPoint(float(self.width())/2.0, float(self.height())/2.0)

        QToolTip.showText(sum_pos, self.text, self)

    def hide_tool_tip(self, e):
        QToolTip.hideText()

class DndFrame(QGroupBox):
    def __init__(self, text):
        QFrame.__init__(self, text)

        self.grid_scroll_area = PyQtExtras.GridScrollArea(self)

        self.text = text

        self.child_set = dict()

        self.setAcceptDrops(True)

    def find_label(self):
        for child in self.child_set.values():
            if child.underMouse():
                return child

        return None

    def add_label(self, text):
        if text not in self.child_set:

            label = DndPlotFile(text)

            self.grid_scroll_area.add_widget_by_label(label)

            self.child_set[text] = label

    def remove_label(self, text):

        label = self.child_set[text] if text in self.child_set else None
        if label != None:
            self.child_set.pop(text)

            self.grid_scroll_area.remove_widget_by_label(label)

            return True
        return False

    def mousePressEvent(self, me):
        if me.button() == Qt.LeftButton:
            child = self.find_label()
            if child != None:
                mime_data = QMimeData()
                mime_data.setData('text/plain', child.get_text())
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                #drag.setHotSpot(child.pos())
                drag_action = drag.exec_(Qt.CopyAction | Qt.MoveAction)

    def dragEnterEvent(self, me):
        me.acceptProposedAction()

    def dragMoveEvent(self, me):
        if me.mimeData().hasFormat('text/plain'):
            me.acceptProposedAction()

    def dropEvent(self, me):

        if me.source() == self and me.possibleActions() & Qt.MoveAction:
            return
        if isinstance(me.source(), DndFrame) and (me.proposedAction() == Qt.MoveAction or me.proposedAction() == Qt.CopyAction):
            me.acceptProposedAction()
            text = str(me.mimeData().retrieveData('text/plain', QVariant.String))
            if me.source().remove_label(text):
                self.add_label(text)

    def get_output_plot_filenames(self):
        output_plot_filenames = list()
        for plot_filename in self.child_set.keys():
            output_plot_filenames.append(plot_filename)

        return output_plot_filenames

class DualFrame(QFrame):

    def __init__(self, plot_title, finish_creating_plot_gui, is_top_level):
        QFrame.__init__(self)

        self.setWindowTitle(plot_title)

        self.main_layout = QVBoxLayout(self)

        self.splitter = QSplitter()
        self.dnd_frame_1 = DndFrame('Output Graphs')
        self.dnd_frame_2 = DndFrame('Graphs to Display')

        self.splitter.addWidget(self.dnd_frame_1)
        self.splitter.addWidget(self.dnd_frame_2)

        self.main_layout.addWidget(self.splitter)

        self.button_layout = QHBoxLayout()

        self.dnd_close_button = PyQtExtras.CommandButton('Close')
        self.dnd_close_button.set_handler(self.on_close)

        self.dnd_accept_button = PyQtExtras.CommandButton('Accept')
        self.dnd_accept_button.set_handler(self.on_accept)

        self.button_layout.addWidget(self.dnd_close_button)
        self.button_layout.addWidget(self.dnd_accept_button)

        self.button_layout.setAlignment(Qt.AlignRight)

        self.main_layout.addLayout(self.button_layout)

        self.finish_creating_plot_gui = finish_creating_plot_gui

        self.is_top_level = is_top_level

        self.setMinimumSize(QSize(800, 640))

    def add_to_first(self, text):
        self.dnd_frame_1.add_label(text)

    def add_to_second(self, text):
        self.dnd_frame_2.add_label(text)

    def on_accept(self):
        plots_to_output = self.dnd_frame_1.get_output_plot_filenames()

        if self.finish_creating_plot_gui != None:
            self.finish_creating_plot_gui(plots_to_output)

        self.close()

    def on_close(self):

        self.hide()

        if self.is_top_level:
            QApplication.exit(0)

def createFrame(plot_title=None, plot_names=list(), finish_creating_plot_gui=None, is_top_level=False):
    main = DualFrame(plot_title, finish_creating_plot_gui, is_top_level)

    for plot_name in plot_names:
        main.add_to_first(plot_name)

    return main

def main(argv):
    app = QApplication([])

    main = createFrame(plot_title='Sample Output', plot_names=['Icon 1', 'Icon 2', 'Icon 3', 'Icon 4', 'Icon 5', 'Icon 6', 'Icon 7'], finish_creating_plot_gui=None, is_top_level=True)
    main.show()

    app.exec_()

if __name__ == '__main__':
    main(sys.argv)
