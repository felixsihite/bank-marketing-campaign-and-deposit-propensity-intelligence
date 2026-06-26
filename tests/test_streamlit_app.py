import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_app_smoke():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=90)
    assert not app.exception
    assert len(app.tabs) == 6
    assert "Bank Marketing Campaign & Deposit Propensity Intelligence" in app.markdown[1].value


def test_streamlit_light_mode_text_contrast_contract():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=90)
    app.radio[0].set_value("Light").run(timeout=90)

    assert not app.exception
    stylesheet = app.markdown[0].value
    assert '[data-testid="stWidgetLabel"] p' in stylesheet
    assert '[data-baseweb="tag"] span' in stylesheet
    assert "#10243D" in stylesheet
    assert "#40516A" in stylesheet

    charts = app.get("plotly_chart")
    assert len(charts) == 14
    for chart in charts:
        layout = json.loads(chart.proto.spec)["layout"]
        assert layout["font"]["color"] == "#10243D"
        assert layout["xaxis"]["tickfont"]["color"] == "#10243D"
        assert layout["xaxis"]["title"]["font"]["color"] == "#10243D"
        assert layout["yaxis"]["tickfont"]["color"] == "#10243D"
        assert layout["yaxis"]["title"]["font"]["color"] == "#10243D"
        assert layout["legend"]["font"]["color"] == "#10243D"