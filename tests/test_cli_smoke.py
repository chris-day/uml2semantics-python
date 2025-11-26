from pathlib import Path
import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "uml2semantics.cli", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "uml2semantics" in result.stdout
