import unittest
import json
from pathlib import Path

from streamlit.testing.v1 import AppTest
from src.data import VARIABLES, NEIGHBORS
from src.selection import selected_graph, toggle_province

APP = Path(__file__).resolve().parents[1] / "app.py"
TRIANGLE = ["Phú Thọ", "Thái Nguyên", "Hà Nội"]


def click_province(at, province):
    # Inject the same trigger payload sent by the custom map's frontend.
    from streamlit.components.v2.bidi_component.main import _make_trigger_id
    states = at._tree.get_widget_states()
    base = states.widgets.add()
    base.id = at.get("bidi_component")[0].proto.id
    base.json_value = "{}"
    widget = states.widgets.add()
    widget.id = _make_trigger_id(at.get("bidi_component")[0].proto.id, "events")
    widget.json_trigger_value = json.dumps([{"event": "clicked", "value": province}])
    return at._run(states)


class SelectionTests(unittest.TestCase):
    def test_toggle_limit_and_induced_graph(self):
        selected = []
        for v in TRIANGLE:
            selected = toggle_province(selected, v, 3, VARIABLES)
        self.assertEqual(toggle_province(selected, "Đồng Tháp", 3, VARIABLES), selected)
        self.assertEqual(toggle_province(selected, "unknown", 3, VARIABLES), selected)
        self.assertEqual(toggle_province(selected, TRIANGLE[0], 3, VARIABLES), TRIANGLE[1:])
        vertices, neighbors = selected_graph(selected, VARIABLES, NEIGHBORS)
        self.assertEqual(set(vertices), set(TRIANGLE))
        for v in vertices:
            self.assertEqual(set(neighbors[v]), set(TRIANGLE) - {v})

    def test_subset_run_replay_compare_reset(self):
        at = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(at.exception)
        at.number_input[0].set_value(3).run()
        self.assertEqual(at.session_state["selected_provinces"], [])
        self.assertTrue(at.button[0].disabled)
        for province in TRIANGLE:
            click_province(at, province)
        self.assertEqual(at.session_state["selected_provinces"], TRIANGLE)
        click_province(at, "Đồng Tháp")
        self.assertEqual(at.session_state["selected_provinces"], TRIANGLE)
        at.button[0].click().run()
        self.assertFalse(at.exception)
        k, result = at.session_state["runs"][-1]
        self.assertEqual(k, 3)
        self.assertEqual(set(result.solution), set(TRIANGLE))
        at.checkbox[0].check().run()
        at.slider(key="step").set_value(1).run()
        self.assertFalse(at.exception)
        at.radio[0].set_value("Thử số màu cố định").run()
        self.assertTrue(at.button[0].disabled)  # 10 colors cannot fit 3 provinces.
        self.assertIsNone(at.session_state["runs"])
        at.slider[0].set_value(3).run()
        at.button[0].click().run()
        self.assertEqual(len(set(at.session_state["runs"][-1][1].solution.values())), 3)
        at.button[1].click().run()
        self.assertEqual([r["Trạng thái"] for r in at.session_state["comparison"]], ["solved"] * 3)
        click_province(at, TRIANGLE[0])
        self.assertEqual(at.session_state["selected_provinces"], TRIANGLE[1:])
        self.assertIsNone(at.session_state["runs"])
        self.assertIsNone(at.session_state["comparison"])
        at.button[2].click().run()
        self.assertEqual(at.session_state["selected_provinces"], [])
        self.assertIsNone(at.session_state["runs"])
        self.assertIsNone(at.session_state["comparison"])
        self.assertTrue(at.button[0].disabled)
        self.assertFalse(at.exception)


if __name__ == "__main__":
    unittest.main()
