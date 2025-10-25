
import subprocess, threading, datetime, os
from pathlib import Path

class ProcessRunner:
    def __init__(self, results_dir: Path):
        self.results_dir = results_dir
        self.proc = None
        self.log_path = None

    def start(self, args, line_cb, env=None):
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.log_path = self.results_dir / f"log_run_{ts}.txt"
        self.results_dir.mkdir(exist_ok=True, parents=True)
        def worker():
            try:
                self.proc = subprocess.Popen([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
                with self.log_path.open("a", encoding="utf-8") as f:
                    for line in self.proc.stdout:
                        f.write(line)
                        line_cb(line)
                rc = self.proc.wait()
                line_cb(f"[EXIT] {rc}\n")
            except FileNotFoundError:
                line_cb("[ERROR] .venv\\Scripts\\python.exe not found. Run setup_env.bat first.\n")
            except Exception as e:
                line_cb(f"[ERROR] {e!r}\n")
        threading.Thread(target=worker, daemon=True).start()

    def terminate(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
