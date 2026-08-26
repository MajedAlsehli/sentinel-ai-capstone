from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_without_starting_an_investigation():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=15)
    app.run()

    assert not app.exception
    assert any("Investigate with evidence" in item.value for item in app.markdown)
    assert app.selectbox[0].label == "Load an investigation example"
    assert app.text_area[0].label == "Artifact or investigation request"
    assert any(button.label == "Run agentic investigation" for button in app.button)
    assert app.sidebar.text_input[0].value == "Majed Alsehli"
    assert app.sidebar.toggle[0].value is True
