from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys


class Window(QMainWindow):
    def __int__(self):
        super(Window, self).__init__()

        self.setWindowTitle("Test")
        self.setGeometry(300, 250, 350, 200)

        self.main_test = QtWidgets.QLabel(self)
        self.main_test.setText("Test")
        self.main_test.move(100, 100)
        self.main_test.adjustSize()

        self.btn = QtWidgets.QPushButton(self)
        self.btn.move(50, 30)
        self.btn.setText('NEXT')
        self.btn.setFixedWidth(100)
        self.btn.clicked.connect(self.add_label)

    def add_label(self):
        print('add')


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
