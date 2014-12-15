import PyQtExtras

from PyQt5.QtWidgets import QFrame, QApplication

import sys

def main(args):
    app = QApplication([])

    main_frame = QFrame()

    list_view = PyQtExtras.ListScrollArea(main_frame)

    list_view.add_item_by_string('Item 1')
    list_view.add_item_by_string('Item 2')
    list_view.add_item_by_string('Item 3')

    list_view.remove_item_by_string('Item 1')

    main_frame.show()

    app.exec_()

if __name__ == '__main__':
    main(sys.argv)