import subprocess

from .conftest import SUBMISSION


def test_clean_destroy(deployment):
    subprocess.run([str(SUBMISSION / "destroy.sh")], cwd=SUBMISSION, check=True, timeout=900)
    result = subprocess.run(
        ["terraform", f"-chdir={SUBMISSION / 'infra'}", "state", "list"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert not result.stdout.strip()
