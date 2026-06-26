import json
import os
from pathlib import Path
import tomllib
from typing import Any

import matplotlib
import nbformat
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def _all_strings(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _all_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_strings(nested)
    elif isinstance(value, str):
        yield value


def _relative_luminance(hex_color):
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first, second):
    high, low = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_notebooks_are_executable_and_reconciled():
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    notebook_paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
    assert [path.name for path in notebook_paths] == [
        "01_data_quality_and_campaign_eda.ipynb",
        "02_propensity_model_validation.ipynb",
        "03_executive_intelligence_review.ipynb",
    ]

    original_directory = Path.cwd()
    original_show = plt.show
    os.chdir(ROOT)
    try:
        plt.show = lambda: None
        for notebook_path in notebook_paths:
            notebook = nbformat.read(notebook_path, as_version=4)
            assert str(notebook.metadata.language_info.version).startswith("3.11")
            assert len(notebook.cells) >= 6
            namespace: dict[str, Any] = {"__name__": "__notebook_test__"}
            for index, cell in enumerate(notebook.cells):
                if cell.cell_type == "code":
                    exec(compile(cell.source, f"{notebook_path.name}:cell-{index}", "exec"), namespace)
            notebook_assertions = namespace.get("notebook_assertions")
            assert isinstance(notebook_assertions, dict)
            assert all(bool(value) for value in notebook_assertions.values())
    finally:
        plt.show = original_show
        os.chdir(original_directory)


def test_visual_themes_have_dark_and_nonwhite_light_palettes():
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert config["theme"]["base"] == "dark"
    assert config["theme"]["light"]["backgroundColor"] == "#CEC8E3"
    assert config["theme"]["dark"]["backgroundColor"] == "#071A2E"

    theme_files = sorted((ROOT / "powerbi").glob("theme*.json"))
    assert [path.name for path in theme_files] == ["theme.json"]
    theme = json.loads(theme_files[0].read_text(encoding="utf-8"))
    colors = {item.upper() for item in _all_strings(theme) if item.startswith("#")}
    assert "#FFFFFF" not in colors
    assert theme["background"].upper() == "#CEC8E3"
    assert _contrast_ratio("#CEC8E3", "#FFFFFF") >= 1.5
    assert _contrast_ratio("#CEC8E3", "#0B1F3A") >= 10
    assert _contrast_ratio("#0B1F3A", "#CEC8E3") >= 7
    assert _contrast_ratio("#40516A", "#CEC8E3") >= 4.5


def test_requirements_separate_runtime_from_development_tools():
    runtime_requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    development_requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()

    assert runtime_requirements == [
        "pandas==2.2.3",
        "streamlit==1.54.0",
        "plotly==6.5.2",
    ]
    assert "jupyter==1.1.1" not in development_requirements
    assert any(item.startswith("ipykernel==") for item in development_requirements)
    assert any(item.startswith("nbformat==") for item in development_requirements)


def test_public_repository_structure_is_curated():
    assert sorted(path.name for path in (ROOT / "docs").iterdir()) == ["business_recommendations.md"]
    assert not (ROOT / "run.ps1").exists()
    assert not (ROOT / "runtime.txt").exists()
    assert not (ROOT / "outputs" / "charts").exists()

    screenshots = sorted((ROOT / "outputs" / "dashboard_screenshots").glob("*.png"))
    assert [path.name for path in screenshots] == [
        "01_executive_overview.png",
        "02_customer_profile_intelligence.png",
        "03_campaign_optimization.png",
        "04_propensity_decision_support.png",
    ]
    for screenshot in screenshots:
        with Image.open(screenshot).convert("RGB") as image:
            assert image.getpixel((0, 0)) == (206, 200, 227)
