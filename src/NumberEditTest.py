import PyQtExtras
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QFrame
import sys

def main(args):
    app = QApplication([])

    main_frame = QFrame()

    layout = QVBoxLayout(main_frame)

    number_edit = PyQtExtras.NumberEdit()
    number_edit.set_value(10)
    print 'Current value of 1 is: ' + str(number_edit.get_value())

    number_edit2 = PyQtExtras.NumberEdit(max_length=2)
    number_edit2.set_value(2)
    print 'Current value of 2 is: ' + str(number_edit2.get_value())
    number_edit2.set_value(20)
    print 'Current value of 2 is: ' + str(number_edit2.get_value())

    number_edit3 = PyQtExtras.NumberEdit(max_length=1)
    number_edit3.set_value(2)
    print 'Current value of 3 is: ' + str(number_edit3.get_value())
    number_edit3.set_value(50)
    print 'Current values of 3 is: ' + str(number_edit3.get_value())
    number_edit3.set_value(25)
    print 'Current value of 3 is: ' + str(number_edit3.get_value())
    number_edit3.set_value('text')
    print 'Current value of 3 is: ' + str(number_edit3.get_value())

    layout.addWidget(number_edit)
    layout.addWidget(number_edit2)
    layout.addWidget(number_edit3)

    main_frame.show()

    app.exec_()

if __name__ == '__main__':
    main(sys.argv)