from PySide6 import QtWidgets
from .app import MainWindow

def main():
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.resize(800, 600)
    w.show()
    app.exec()

if __name__ == '__main__':
    main()
