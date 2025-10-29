import subprocess, sys, os

# Proste pakowanie na Windows z PyInstaller (zainstaluj: pip install pyinstaller)
# Użycie: python scripts/package_win.py

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))

if __name__ == '__main__':
    os.chdir(ROOT)
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconsole', '--onefile', '--name', 'ElBotto', '-m', 'elbotto.__main__']
    print('Running:', ' '.join(cmd))
    sys.exit(subprocess.call(cmd))
