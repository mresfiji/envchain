"""Tests for envchain.broadcaster."""

from pathlib import Path
import json
import pytest

from envchain.broadcaster import (
    BroadcastTarget,
    BroadcastError,
    broadcast,
)


VARS = {"API_KEY": "secret123", "DEBUG": "true"}


def test_broadcast_shell_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "env.sh"
    targets = [BroadcastTarget(format="shell", path=out, label="shell-out")]
    result = broadcast(VARS, targets)
    assert not result.has_failures
    assert "shell-out" in result.succeeded
    content = out.read_text()
    assert "export API_KEY=" in content


def test_broadcast_dotenv_writes_file(tmp_path: Path) -> None:
    out = tmp_path / ".env"
    targets = [BroadcastTarget(format="dotenv", path=out)]
    result = broadcast(VARS, targets)
    assert not result.has_failures
    content = out.read_text()
    assert "API_KEY=" in content


def test_broadcast_json_writes_valid_json(tmp_path: Path) -> None:
    out = tmp_path / "env.json"
    targets = [BroadcastTarget(format="json", path=out)]
    result = broadcast(VARS, targets)
    assert not result.has_failures
    data = json.loads(out.read_text())
    assert data["API_KEY"] == "secret123"


def test_broadcast_multiple_targets(tmp_path: Path) -> None:
    targets = [
        BroadcastTarget(format="shell", path=tmp_path / "env.sh", label="sh"),
        BroadcastTarget(format="dotenv", path=tmp_path / "sub" / ".env", label="dotenv"),
        BroadcastTarget(format="json", path=tmp_path / "env.json", label="json"),
    ]
    result = broadcast(VARS, targets)
    assert len(result.succeeded) == 3
    assert not result.has_failures
    assert (tmp_path / "sub" / ".env").exists()


def test_broadcast_no_targets_raises() -> None:
    with pytest.raises(BroadcastError, match="No broadcast targets"):
        broadcast(VARS, [])


def test_broadcast_invalid_format_raises(tmp_path: Path) -> None:
    with pytest.raises(BroadcastError, match="Unsupported broadcast format"):
        BroadcastTarget(format="xml", path=tmp_path / "out.xml")


def test_broadcast_io_error_captured(tmp_path: Path) -> None:
    # Point to a path that cannot be created (file used as directory)
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    bad_path = blocker / "env.sh"  # blocker is a file, not a dir
    targets = [BroadcastTarget(format="shell", path=bad_path, label="bad")]
    result = broadcast(VARS, targets)
    assert result.has_failures
    assert "bad" in result.failed


def test_summary_includes_failure_reason(tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    bad_path = blocker / "env.sh"
    targets = [BroadcastTarget(format="shell", path=bad_path, label="bad-target")]
    result = broadcast(VARS, targets)
    summary = result.summary()
    assert "FAILED" in summary
    assert "bad-target" in summary
