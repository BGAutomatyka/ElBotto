from PySide6 import QtWidgets, QtCore, QtGui
import subprocess, json, os
from pathlib import Path

CFG_PATH = os.path.expanduser('~/.elbotto/config.json')

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
        self.btn_report = QtWidgets.QPushButton("Otwórz raport")
        for b in (self.btn_backtest, self.btn_live, self.btn_stop, self.btn_report):
            layout.addWidget(b)
        layout.addWidget(self.status)
        self.proc: subprocess.Popen | None = None
        self.btn_backtest.clicked.connect(self.start_backtest)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_report.clicked.connect(self.open_report)
        self.timer = QtCore.QTimer(self); self.timer.setInterval(500); self.timer.timeout.connect(self.poll)
        self.timer.start()
        self.last_cwd = os.getcwd()

    def load_cfg(self):
        if os.path.exists(CFG_PATH):
            try:
                return json.load(open(CFG_PATH))
            except Exception:
                return {}
        return {}

    def start_backtest(self):
        csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Wybierz CSV z danymi (timestamp,open,high,low,close,volume)", filter="CSV (*.csv)")
        if not csv_path:
            return
        cfg = self.load_cfg()
        cmd = cfg.get('backtest_cmd')
        if not cmd:
            QtWidgets.QMessageBox.information(self, 'Konfiguracja', 'Skonfiguruj backtest_cmd w ~/.elbotto/config.json (np. "python ..\ElBo\scripts\run_backtest.py")')
            return
        self.status.setText('Backtest uruchomiony...')
        self.proc = subprocess.Popen([cmd, '--csv', csv_path, '--out', 'trades.csv', '--report_dir', 'report'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.last_cwd = os.path.dirname(csv_path) or os.getcwd()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.status.setText('Zatrzymano')

    def poll(self):
        if not self.proc: return
        if self.proc.stdout:
            line = self.proc.stdout.readline()
            if line:
                self.status.setText(line.strip())
        if self.proc.poll() is not None:
            self.status.setText('Zakończono: trades.csv / equity.csv / report/report.html')
            self.proc = None

    def open_report(self):
        # próbuj otworzyć raport z bieżącego folderu pracy
        paths = [
            Path(self.last_cwd)/'report'/'report.html',
            Path(os.getcwd())/'report'/'report.html'
        ]
        for p in paths:
            if p.exists():
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(p)))
                return
        QtWidgets.QMessageBox.information(self, 'Raport', 'Nie znaleziono report/report.html')

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.resize(800, 600)
    w.show()
    app.exec()
