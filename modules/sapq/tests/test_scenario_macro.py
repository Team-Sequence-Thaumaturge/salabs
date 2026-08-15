import json
import unittest
import tempfile
import os
from modules.sapq.sapq_dom_relay import SAPQDOMRelay

class TestSAPQDOMRelayScenario(unittest.TestCase):
    def setUp(self):
        self.html_content = """
        <html>
        <body>
            <input type="text" id="input1" />
            <div id="res" style="display: none;"></div>
            <script>
                function handleSubmit() {
                    const val = document.getElementById('input1').value;
                    const res = document.getElementById('res');
                    if (val === 'test') {
                        res.innerText = 'Success';
                        res.style.display = 'block';
                    }
                }
            </script>
            <button id="btn1" onclick="handleSubmit()">Submit</button>
        </body>
        </html>
        """
        self.fd, self.temp_path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(self.fd, 'w') as f:
            f.write(self.html_content)
        self.relay = SAPQDOMRelay(self.temp_path)

    def tearDown(self):
        os.remove(self.temp_path)

    def test_execute_scenario(self):
        scenario = [
            {"action": "fill", "selector": "#input1", "value": "test"},
            {"action": "click", "selector": "#btn1"},
            {"action": "assert_text", "selector": "#res", "expected": "Success"},
            {"action": "assert_style", "selector": "#res", "property": "display", "expected": "block"}
        ]
        res = self.relay.execute_scenario(scenario)
        self.assertTrue(res['scenario_completed'])
        self.assertEqual(len(res['steps']), 4)
        self.assertTrue(res['dom_delta']['changed'])

if __name__ == '__main__':
    unittest.main()
