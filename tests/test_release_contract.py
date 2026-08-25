"""Tests for the distributable v1.0 release contract."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_manifest_and_hacs_metadata_are_release_ready():
    manifest = json.loads((ROOT / "custom_components/wfd/manifest.json").read_text())
    hacs = json.loads((ROOT / "hacs.json").read_text())

    assert manifest["version"] == "1.0.0"
    assert manifest["config_flow"] is True
    assert hacs["render_readme"] is True


def test_v1_documentation_covers_installation_api_and_decisions():
    for path in (
        ROOT / "README.md",
        ROOT / "docs/installation.md",
        ROOT / "docs/services.md",
        ROOT / "docs/decision-engine.md",
    ):
        assert path.exists()
        assert path.read_text().strip()
