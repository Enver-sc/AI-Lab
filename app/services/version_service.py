import subprocess

from config import BASE_DIR


def get_app_version() -> str:
    """Git-basierte Versionskennung statt eines manuell gepflegten Versionsfelds --
    das kann bei einem Merge in die Mainline nicht vergessen werden, weil niemand es
    pflegen muss. Faellt auf 'unbekannt' zurueck, wenn kein Git verfuegbar ist (z. B.
    gepackte Auslieferung ohne .git-Ordner)."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip() or "unbekannt"
    except (subprocess.SubprocessError, OSError):
        return "unbekannt"
