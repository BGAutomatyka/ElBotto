ElBotto Link Pack — szybkie podłączenie repo, pull i wysyłka wyników (Windows)

1) Skopiuj WSZYSTKIE pliki z tego archiwum do katalogu głównego repo ElBotto.
2) Dwuklik: ELBOTTO_ONE_CLICK_SETUP.bat  (postawi .venv, doda narzędzia i menu)
3) Dwuklik: GIT_SETUP_OR_CONNECT.bat     (połączy folder z GitHub: https://github.com/BGAutomatyka/ElBotto )
4) Zmiany z GitHuba pobierasz klikając:  PULL_FROM_GITHUB.bat
5) Żeby dać mi dostęp do wyników (results/): uruchom PUSH_RESULTS.bat
   - skrypt zrobi gałąź runs/YYYYMMDD_HHMMSS, doda results/* (nawet jeśli są w .gitignore), wypchnie na GitHuba.
   - UWAGA: nie wrzucaj do results/ żadnych sekretów.

Opcjonalnie:
- AUTO_PULL_WATCH.ps1 – autopull co X minut w pętli (uruchamiasz w PowerShellu).
