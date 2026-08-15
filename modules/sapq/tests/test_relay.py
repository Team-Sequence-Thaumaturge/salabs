import json
import unittest
import tempfile
import os
from modules.sapq.sapq_dom_relay import SAPQDOMRelay

class TestSAPQDOMRelay(unittest.TestCase):
    def setUp(self):
        self.html_content = """
        <html>
        <body>
            <div id="content_m1" style="display: none;">Hello World</div>
            <script>
                function toggleAccordion(id) {
                    console.log("Toggling " + id);
                    const el = document.getElementById(id);
                    if (el) {
                        el.style.display = el.style.display === 'none' ? 'block' : 'none';
                    } else {
                        console.error("Element not found: " + id);
                    }
                }
            </script>
            <button id="btn1" onclick="toggleAccordion('content_m1')">OK</button>
            <button id="btn2" onclick="toggleAccordion('content_missing')">BAD</button>
        </body>
        </html>
        """
        self.fd, self.temp_path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(self.fd, 'w') as f:
            f.write(self.html_content)
        self.relay = SAPQDOMRelay(self.temp_path)

    def tearDown(self):
        os.remove(self.temp_path)

    def test_generate_navigation_map(self):
        nav_map = self.relay.generate_navigation_map()
        self.assertEqual(len(nav_map), 2)
        self.assertEqual(nav_map[0]['id'], 'btn1')
        self.assertEqual(nav_map[0]['onclick'], "toggleAccordion('content_m1')")

    def test_dispatch_valid_event(self):
        res = self.relay.dispatch_event_and_capture('#btn1')
        self.assertTrue(res['success'])
        self.assertTrue(res['dom_delta']['changed'])
        self.assertEqual(len(res['console_messages']), 1)
        self.assertEqual(res['console_messages'][0]['text'], 'Toggling content_m1')

    def test_dispatch_invalid_event(self):
        res = self.relay.dispatch_event_and_capture('#btn2')
        self.assertTrue(res['success'])
        self.assertFalse(res['dom_delta']['changed'])
        self.assertEqual(len(res['console_messages']), 2)
        self.assertEqual(res['console_messages'][1]['type'], 'error')
        self.assertTrue("Element not found: content_missing" in res['console_messages'][1]['text'])

if __name__ == '__main__':
    unittest.main()
