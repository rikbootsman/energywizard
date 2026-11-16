import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "ha-addon" / "smartbox"


@pytest.mark.parametrize("options,expected", [
    (None, "true"),
    ({}, "true"),
    ({"shadow_mode": True}, "true"),
    ({"shadow_mode": False}, "false"),
])
def test_addon_forces_shadow_before_starting_any_process(tmp_path, options, expected):
    path = tmp_path / "options.json"
    if options is not None:
        path.write_text(json.dumps(options))
    startup = (ADDON / "rootfs" / "run.sh").read_text()
    preflight = startup.split('OPTIONS="/data/options.json"\n', 1)[1].split("# Som HA", 1)[0]
    env = {key: value for key, value in os.environ.items() if key != "SHADOW_MODE"}
    result = subprocess.run(
        ["bash", "-ec", f'OPTIONS="$1"\n{preflight}\nprintf "%s" "$SHADOW_MODE"', "test", str(path)],
        env=env, capture_output=True, text=True, check=True,
    )
    assert result.stdout == expected


def test_supervisor_builds_the_privacy_fork_not_the_upstream_image():
    config = yaml.safe_load((ADDON / "config.yaml").read_text())
    dockerfile = (ADDON / "Dockerfile").read_text()
    assert "image" not in config
    assert config["options"]["shadow_mode"] is True
    assert "ARG ENERGYWIZARD_REPO=https://github.com/rikbootsman/energywizard\n" in dockerfile
    assert "ARG ENERGYWIZARD_REF=privacy-1\n" in dockerfile
