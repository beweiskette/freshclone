# FreshClone

Prüft ausgewählte README-Befehle in einem frischen, eingeschränkten Docker-Container. Fehler werden dem Codeblock und seiner README-Zeile zugeordnet.

Erste nutzbare Version 0.1.0. Python ab 3.11, MIT-Lizenz. Vollständige Schnittstellen und Beispiele stehen in der [englischen README](README.md).

## Installation

Im geklonten Repo eine virtuelle Umgebung anlegen:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

## Beispiel

```sh
freshclone inspect ./your-project
freshclone run ./your-project --blocks 1,2 --image python:3.11-slim --out outputs/check
```

Berichte entstehen als `report.json` und `report.html` im gewählten Ausgabeordner. Rückgabecode 0 bedeutet bestanden, 1 bedeutet Befunde, 2 einen Eingabe- oder Laufzeitfehler. Die Beispieldaten sind künstlich.

Der Container erbt keine Host-Umgebungsvariablen. Netzwerk ist standardmässig aus. Nur von Git erfasste Arbeitsdateien werden übertragen. Jeder Block läuft in einer eigenen POSIX-Shell; Dateien bleiben zwischen Blöcken erhalten. Bash-Sondersyntax und gemeinsame Shell-Variablen über mehrere Blöcke sind nicht unterstützt. Die Dateinamensperre ersetzt keinen Secret-Scanner.

Tests: `python -m pytest -q`. Für Docker- und Browsertests gelten die zusätzlichen Voraussetzungen in der englischen README. Das Werkzeug lädt keine Berichte hoch und ruft keine Modell-API auf.
