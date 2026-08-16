import json
import unittest
import tempfile
import os
import urllib.request
from modules.sapq.sapq_sandbox_proxy import SAPQSandboxProxy
from modules.sapq.sapq_agent_protocol import SAPQAgentProtocol

class TestProxyAndProtocol(unittest.TestCase):
    def setUp(self):
        self.html_content = """
        <html>
        <body>
            <div id="content_m1" style="display: none;">Hello World</div>
            <button id="btn1" onclick="document.getElementById('content_m1').style.display='block';">OK</button>
        </body>
        </html>
        """
        # Create temp file in current directory to make it easier for proxy to serve
        self.temp_filename = "test_proxy_temp.html"
        with open(self.temp_filename, 'w') as f:
            f.write(self.html_content)

    def tearDown(self):
        if os.path.exists(self.temp_filename):
            os.remove(self.temp_filename)

    def test_sandbox_proxy(self):
        proxy = SAPQSandboxProxy(port=8081)
        proxy.start()

        url = proxy.get_url(self.temp_filename)
        self.assertTrue(url.startswith("http://localhost:8081/"))

        # Test HTTP fetch
        response = urllib.request.urlopen(url)
        content = response.read().decode('utf-8')
        self.assertTrue("Hello World" in content)

        proxy.stop()

    def test_agent_protocol(self):
        protocol = SAPQAgentProtocol(self.temp_filename, proxy_port=8082)

        nav_response = json.loads(protocol.request_navigation_map())
        self.assertEqual(nav_response["status"], "success")
        self.assertTrue(len(nav_response["data"]["navigation_map"]) > 0)

        action_response = json.loads(protocol.dispatch_action("#btn1"))
        self.assertEqual(action_response["status"], "success")
        self.assertTrue(action_response["data"]["delta"]["changed"])

        protocol.shutdown()

if __name__ == '__main__':
    unittest.main()
