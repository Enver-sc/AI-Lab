import subprocess
from unittest.mock import patch

from app.services.version_service import get_app_version


def test_returns_real_git_output_in_this_repo():
    # Dieses Projekt ist selbst ein Git-Repository -- kein Mock noetig, um den
    # Regelfall zu pruefen.
    version = get_app_version()
    assert version and version != "unbekannt"


def test_falls_back_when_git_is_unavailable():
    with patch("app.services.version_service.subprocess.run", side_effect=FileNotFoundError()):
        assert get_app_version() == "unbekannt"


def test_falls_back_on_subprocess_error():
    with patch("app.services.version_service.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
        assert get_app_version() == "unbekannt"
