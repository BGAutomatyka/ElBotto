from PySide6 import QtWidgets
from elbotto.keys import ApiKeys, CRED_PATH

class KeysDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
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

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    dlg = KeysDialog()
    dlg.show()
    app.exec()
