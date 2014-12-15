
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QScrollArea, QFrame, QGridLayout, QListView, QCheckBox, QLineEdit
from PyQt5.QtCore import pyqtSignal, QStringListModel
from PyQt5.QtGui import QPalette, QColor
from PyQt5.Qt import Qt

class NumberEdit(QLineEdit):
    def __init__(self, max_length=100):
        QLineEdit.__init__(self)

        mask = '9' * max_length

        self.setInputMask(mask)

    def set_value(self, value):
        self.insert(str(value))

    def get_value(self):
        return int(self.text())

    def textChanged(self, text):
        print('Text changed to: ' + text)

class CommandCheckBox(QCheckBox):
    checked_event_handler = pyqtSignal()
    unchecked_event_handler = pyqtSignal()
    def set_handlers(self, checked_slot, unchecked_slot):
        self.checked_event_handler.connect(checked_slot)
        self.unchecked_event_handler.connect(unchecked_slot)
    def stateChanged(self, state):
        if state == Qt.Checked:
            self.checked_event_handler.emit()
        else:
            self.unchecked_event_handler.emit()
    def set_state(self, checked):
        state = Qt.Checked
        if not checked:
            state = Qt.Unchecked
        self.setCheckState(state)

class CommandButton(QPushButton):
    event_handler = pyqtSignal()
    def set_handler(self, slot):
        self.event_handler.connect(slot)
    def mouseReleaseEvent(self, me):
        self.event_handler.emit()

class GridScrollArea(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self, parent)

        self.scroll_area = QScrollArea()

        self.grid_frame = QFrame(self.scroll_area)

        self.grid_layout = QGridLayout(self.grid_frame)

        self.scroll_area.setWidget(self.grid_frame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setBackgroundRole(QPalette.Light)

        self.addWidget(self.scroll_area)

        self.current_column = 0

        self.current_row = 0

        self.initial_grid = True

        self.max_columns = 5

        self.current_width = 0

        self.child_widgets = list()

    def add_widget_by_label(self, label):
        if label != None:
            self.grid_layout.addWidget(label, self.current_row, self.current_column)

            print('Added to row: ' + str(self.current_row))
            print('Added to column: ' + str(self.current_column))

            self.grid_frame.updateGeometry()

            self.child_widgets.append(label)

            # Update the row and column indices appropriately
            self.current_column += 1

            if self.current_column == self.max_columns:
                self.current_column = 0
                self.current_row += 1

            self.print_width()

    def remove_widget_by_label(self, label):
        if label != None:
            self.grid_layout.removeWidget(label)

            label.deleteLater()

            self.grid_frame.updateGeometry()

            self.child_widgets.remove(label)

            # Update the row and column indices appropriately
            self.current_column -= 1

            if self.current_column < 0 and self.current_row > 0:
                self.current_column = self.max_columns
                self.current_row -= 1
            elif self.current_column < 0:
                self.current_column = 0

            for child in self.child_widgets:
                self.grid_layout.removeWidget(child)

            current_column = 0
            current_row = 0
            for child in self.child_widgets:
                self.grid_layout.addWidget(child, current_row, current_column)
                current_column += 1
                if current_column == self.max_columns:
                    current_column = 0
                    current_row += 1

    def print_width(self, label=None):
        print('Width of grid frame: ' + str(self.grid_frame.width()))
        #print 'Width of grid layout: ' + str(self.grid_layout.width())
        print('Width of scrolled area: ' + str(self.scroll_area.width()))
        print('Width of vbox layout: ' + str(self.scroll_area.width()))
        if label != None:
            print('Width of new label: ' + str(label.width()))

class ListScrollArea(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self, parent)

        self.scroll_area = QScrollArea()

        # A ListView is a widget, instead of a layout, so there should be no need for additional containers
        self.list_view = QListView()

        self.scroll_area.setWidget(self.list_view)

        self.addWidget(self.list_view)

        self.view_model = QStringListModel()

        self.list_view.setModel(self.view_model)

    def add_item_by_string(self, value):
        current_values = self.view_model.stringList()
        if value not in current_values:
            current_values.append(value)

        self.view_model.setStringList(current_values)

    def remove_item_by_string(self, value):
        current_values = self.view_model.stringList()
        if value in current_values:
            current_values.remove(value)
        self.view_model.setStringList(current_values)

    def clear_all(self):
        self.view_model.setStringList([])

    def get_currently_selected_item(self):
        currently_selected_item_index = self.view_model.currentIndex()
        currently_selected_item_text = str(self.list_view.data(currently_selected_item_index))
        return currently_selected_item_text

    def get_item(self, index):
        current_values = self.view_model.stringList()
        if index < len(current_values):
            return current_values[index]
        return None

    def get_num_items(self):
        return len(self.view_model.stringList())
