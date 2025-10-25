import subprocess, shlex, threading, queue, os
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class ProcInfo:
    cmd: str
    popen: Optional[subprocess.Popen] = None
    output: List[str] = field(default_factory=list)
    rc: Optional[int] = None

class ProcManager:
    def __init__(self):
        self.procs: List[ProcInfo] = []

    def start(self, cmd: str, capture=True) -> ProcInfo:
        info = ProcInfo(cmd=cmd)
        self.procs.append(info)
        if capture:
            p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            info.popen = p
            def _reader():
                for line in p.stdout:
                    info.output.append(line.rstrip())
                info.rc = p.wait()
            threading.Thread(target=_reader, daemon=True).start()
        else:
            p = subprocess.Popen(shlex.split(cmd))
            info.popen = p
        return info

    def kill_all(self):
        for info in self.procs:
            try:
                if info.popen and info.popen.poll() is None:
                    info.popen.terminate()
            except Exception:
                pass

    def cleanup(self):
        self.procs = [i for i in self.procs if not (i.popen and i.popen.poll() is not None)]
