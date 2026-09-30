# FreshClone

PrÃ¼ft ausgewÃ¤hlte README-Befehle in einem frischen, eingeschrÃ¤nkten Docker-Container. Fehler werden dem Codeblock und seiner README-Zeile zugeordnet.

Erste nutzbare Version 0.1.0. Python ab 3.11, MIT-Lizenz. VollstÃ¤ndige Schnittstellen und Beispiele stehen in der [englischen README](README.md).

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

Berichte entstehen als `report.json` und `report.html` im gewÃ¤hlten Ausgabeordner. RÃ¼ckgabecode 0 bedeutet bestanden, 1 bedeutet Befunde, 2 einen Eingabe- oder Laufzeitfehler. Die Beispieldaten sind kÃ¼nstlich.

Der Container erbt keine Host-Umgebungsvariablen. Netzwerk ist standardmÃ¤ssig aus. Nur von Git erfasste Arbeitsdateien werden Ã¼bertragen. Jeder Block lÃ¤uft in einer eigenen POSIX-Shell; Dateien bleiben zwischen BlÃ¶cken erhalten. Bash-Sondersyntax und gemeinsame Shell-Variablen Ã¼ber mehrere BlÃ¶cke sind nicht unterstÃ¼tzt. Die Dateinamensperre ersetzt keinen Secret-Scanner.

Tests: `python -m pytest -q`. FÃ¼r Docker- und Browsertests gelten die zusÃ¤tzlichen Voraussetzungen in der englischen README. Das Werkzeug lÃ¤dt keine Berichte hoch und ruft keine Modell-API auf.

Die Option `--allow-sensitive` erlaubt einzelne geprüfte Beispieldateien wie `.env.example`. Mit `--memory-mib`, `--work-mib` und `--tmp-mib` lassen sich die Speichergrenzen anpassen. `--tmp-exec` erlaubt bei Bedarf Programme in `/tmp`. Die Bereitschaftsprüfung wiederholt HTTP-Anfragen bis zum Zeitlimit. Berichte enthalten je Block begrenzte Ausgaben und können dadurch vertrauliche Inhalte enthalten. Beim Aufräumen werden auch anonyme Docker-Volumes entfernt.
