from PySide6 import QtWidgets, QtCore

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ElBotto")
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        self.status = QtWidgets.QLabel("Ready")
        self.btn_backtest = QtWidgets.QPushButton("Start Backtest")
        self.btn_live = QtWidgets.QPushButton("Start Live")
        self.btn_stop = QtWidgets.QPushButton("Stop")
        for b in (self.btn_backtest, self.btn_live, self.btn_stop):
            layout.addWidget(b)
        layout.addWidget(self.status)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.resize(800, 600)
    w.show()
    app.exec()
