@echo off
.venv\Scripts\python.exe -m elbotto_patch.adapter.elbotto_runtime_adapter_plus --results results --interval 5 --rules rules.json
pause
