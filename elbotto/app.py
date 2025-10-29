from PySide6 import QtWidgets, QtCore, QtGui
import subprocess, json, os
from pathlib import Path
from .keys import ApiKeys, CRED_PATH

CFG_PATH = os.path.expanduser('~/.elbotto/config.json')

class KeysDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('API Keys (Binance)')
        layout = QtWidgets.QFormLayout(self)
        self.le_key = QtWidgets.QLineEdit()
        self.le_sec = QtWidgets.QLineEdit()
        self.le_sec.setEchoMode(QtWidgets.QLineEdit.Password)
        self.cb_testnet = QtWidgets.QCheckBox('Testnet (sandbox)')
        ak = ApiKeys.load()
        self.le_key.setText(ak.api_key)
        self.le_sec.setText(ak.api_secret)
        self.cb_testnet.setChecked(ak.testnet)
        layout.addRow('API Key', self.le_key)
        layout.addRow('API Secret', self.le_sec)
        layout.addRow(self.cb_testnet)
        self.info = QtWidgets.QLabel(f'Plik: {CRED_PATH}')
        layout.addRow(self.info)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.save)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def save(self):
        ak = ApiKeys(api_key=self.le_key.text().strip(), api_secret=self.le_sec.text().strip(), testnet=self.cb_testnet.isChecked())
        ak.save()
        self.accept()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ElBotto')
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        self.status = QtWidgets.QLabel('Ready')
        self.btn_backtest = QtWidgets.QPushButton('Start Backtest')
        self.btn_optimize = QtWidgets.QPushButton('Strojenie (Optuna)')
        self.btn_heatmap = QtWidgets.QPushButton('Heatmap (stabilność)')
        self.btn_live = QtWidgets.QPushButton('Start Live')
        self.btn_stop = QtWidgets.QPushButton('Stop')
        self.btn_report = QtWidgets.QPushButton('Otwórz raport')
        self.btn_keys = QtWidgets.QPushButton('API Keys')
        for b in (self.btn_backtest, self.btn_optimize, self.btn_heatmap, self.btn_live, self.btn_stop, self.btn_report, self.btn_keys):
            layout.addWidget(b)
        layout.addWidget(self.status)
        self.proc: subprocess.Popen | None = None
        self.btn_backtest.clicked.connect(self.start_backtest)
        self.btn_optimize.clicked.connect(self.start_optimize)
        self.btn_heatmap.clicked.connect(self.start_heatmap)
        self.btn_live.clicked.connect(self.start_live)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_report.clicked.connect(self.open_report)
        self.btn_keys.clicked.connect(self.open_keys)
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

    def open_keys(self):
        KeysDialog(self).exec()

    def start_backtest(self):
        csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Wybierz CSV...', filter='CSV (*.csv)')
        if not csv_path:
            return
        preset_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Wybierz preset YAML (opcjonalnie)', filter='YAML (*.yaml *.yml)')
        cfg = self.load_cfg()
        cmd = cfg.get('backtest_cmd')
        if not cmd:
            QtWidgets.QMessageBox.information(self, 'Konfiguracja', 'Ustaw backtest_cmd w ~/.elbotto/config.json')
            return
        self.status.setText('Backtest uruchomiony...')
        args = [cmd, '--csv', csv_path, '--out', 'trades.csv', '--report_dir', 'report']
        if preset_path:
            args += ['--preset', preset_path]
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.last_cwd = os.path.dirname(csv_path) or os.getcwd()

    def start_optimize(self):
        csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'CSV do strojenia...', filter='CSV (*.csv)')
        if not csv_path: return
        trials, ok = QtWidgets.QInputDialog.getInt(self, 'Optuna', 'Liczba prób', 50, 10, 500, 1)
        if not ok: return
        cfg = self.load_cfg()
        cmd = cfg.get('optimize_cmd')
        if not cmd:
            QtWidgets.QMessageBox.information(self, 'Konfiguracja', 'Ustaw optimize_cmd w ~/.elbotto/config.json')
            return
        self.status.setText('Strojenie (Optuna)...')
        args = [cmd, '--csv', csv_path, '--trials', str(trials), '--out_dir', 'tuned']
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.last_cwd = os.path.dirname(csv_path) or os.getcwd()

    def start_heatmap(self):
        csv_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'CSV do heatmapy...', filter='CSV (*.csv)')
        if not csv_path: return
        cfg = self.load_cfg()
        cmd = cfg.get('heatmap_cmd')
        if not cmd:
            QtWidgets.QMessageBox.information(self, 'Konfiguracja', 'Ustaw heatmap_cmd w ~/.elbotto/config.json (np. "python ..\\ElBo\\scripts\\param_heatmap.py")')
            return
        lb_min, ok = QtWidgets.QInputDialog.getInt(self, 'Heatmap', 'lookback min', 10, 5, 200, 1)
        if not ok: return
        lb_max, ok = QtWidgets.QInputDialog.getInt(self, 'Heatmap', 'lookback max', 60, 10, 500, 1)
        if not ok: return
        zmin, ok = QtWidgets.QInputDialog.getDouble(self, 'Heatmap', 'z_entry min', 0.6, 0.1, 5.0, 2)
        if not ok: return
        zmax, ok = QtWidgets.QInputDialog.getDouble(self, 'Heatmap', 'z_entry max', 2.0, 0.1, 5.0, 2)
        if not ok: return
        self.status.setText('Heatmap...')
        args = [cmd, '--csv', csv_path, '--out', 'report/heatmap_params.png', '--lookback_min', str(lb_min), '--lookback_max', str(lb_max), '--zmin', str(zmin), '--zmax', str(zmax)]
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.last_cwd = os.path.dirname(csv_path) or os.getcwd()

    def start_live(self):
        cfg = self.load_cfg()
        cmd = cfg.get('live_cmd')
        if not cmd:
            QtWidgets.QMessageBox.information(self, 'Konfiguracja', 'Ustaw live_cmd w ~/.elbotto/config.json')
            return
        symbol, ok = QtWidgets.QInputDialog.getText(self, 'Live', 'Symbol', text='BTC/USDT')
        if not ok or not symbol: return
        timeframe, ok = QtWidgets.QInputDialog.getText(self, 'Live', 'Timeframe', text='1m')
        if not ok or not timeframe: return
        preset_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Preset YAML (opcjonalnie)', filter='YAML (*.yaml *.yml)')
        dry = QtWidgets.QMessageBox.question(self, 'Tryb', 'Uruchomić w trybie DRY-RUN?')
        dry_run = (dry == QtWidgets.QMessageBox.StandardButton.Yes)
        args = [cmd, '--symbol', symbol, '--timeframe', timeframe, '--report_dir', 'report_live']
        if preset_path: args += ['--preset', preset_path]
        if dry_run:
            args += ['--dry_run']
        else:
            keys = ApiKeys.load()
            if not keys.api_key or not keys.api_secret:
                QtWidgets.QMessageBox.information(self, 'API Keys', 'Brak kluczy – wypełnij w "API Keys".')
                KeysDialog(self).exec()
                keys = ApiKeys.load()
            if not keys.api_key or not keys.api_secret:
                return
            args += ['--api_key', keys.api_key, '--api_secret', keys.api_secret]
            if keys.testnet: args += ['--testnet']
        self.status.setText('Live start...')
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.last_cwd = os.getcwd()

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
            self.status.setText('Zakończono. Wyniki w report*/ katalogu.')
            self.proc = None

    def open_report(self):
        paths = [
            Path(self.last_cwd)/'report'/'report.html',
            Path(self.last_cwd)/'report_live'/'report.html',
            Path(self.last_cwd)/'report'/'heatmap_params.png',
            Path(os.getcwd())/'report'/'heatmap_params.png',
            Path(os.getcwd())/'report'/'report.html',
            Path(os.getcwd())/'report_live'/'report.html'
        ]
        for p in paths:
            if p.exists():
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(p)))
                return
        QtWidgets.QMessageBox.information(self, 'Raport', 'Nie znaleziono raportu ani heatmapy')
