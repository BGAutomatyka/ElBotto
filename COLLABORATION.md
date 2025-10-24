# Wspólna praca nad ElBotto

Aby uniknąć konfliktów pomiędzy różnymi asystentami (np. ChatGPT i Codex),
korzystajcie ze wspólnej gałęzi roboczej `collab/integration`.

1. **Pobierz najnowsze zmiany**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Pracuj na wspólnej gałęzi**
   ```bash
   git checkout -B collab/integration
   ```
3. **Po zakończeniu zadania** wypchnij zmiany i otwórz PR z gałęzi
   `collab/integration` do `main`. W opisie PR podlinkuj wykonane zadania oraz
   poinformuj drugiego asystenta o nowych plikach.
4. **Komunikacja** – aktualne wyniki auto-testów i raportów zapisuj w katalogu
   `results/` i dodawaj do repozytorium jako część PR, aby druga osoba mogła je
   pobrać bez ponownego uruchamiania.
5. **Konflikty** – przed kolejną iteracją zawsze synchronizuj gałąź:
   ```bash
   git checkout collab/integration
   git pull --rebase origin collab/integration
   ```

Takie podejście zapewnia, że obaj asystenci widzą te same zmiany i łatwiej
kontrolują spójność aplikacji.
