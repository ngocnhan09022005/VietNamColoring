from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_run_replay_persistence_and_comparison():
    at = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert "tối thiểu" in at.success[0].value
    assert at.session_state["runs"][-1][0] == 4
    at.checkbox[0].check().run()
    assert not at.exception
    at.slider(key="step").set_value(2).run()
    assert not at.exception
    assert at.session_state["runs"][-1][1].status == "solved"
    at.button[1].click().run()
    assert not at.exception
    assert len(at.session_state["comparison"]) == 3


def test_fixed_unsatisfiable_and_config_invalidation():
    at = AppTest.from_file(str(APP), default_timeout=20).run()
    at.radio[0].set_value("Thử số màu cố định").run()
    at.slider[0].set_value(2).run()
    at.button[0].click().run()
    assert not at.exception
    assert at.error
    at.slider[0].set_value(4).run()
    assert at.session_state["runs"] is None
    at.button[0].click().run()
    assert not at.exception and at.success

