import unittest
from modules.sapq.sapq_cascade_graph import SAPQCascadeGraph

class TestSAPQCascadeGraph(unittest.TestCase):
    def test_blind_interceptor(self):
        code = """
        function blindUpdate() {
            document.getElementById('display').innerHTML = "Hardcoded Value";
        }
        """
        graph = SAPQCascadeGraph(code=code)
        issues = graph.analyze()
        self.assertTrue(any(i['type'] == 'BLIND_INTERCEPTOR' for i in issues))

    def test_safe_interceptor(self):
        code = """
        const appState = { val: "Safe" };
        function safeUpdate() {
            document.getElementById('display').innerHTML = appState.val;
        }
        """
        graph = SAPQCascadeGraph(code=code)
        issues = graph.analyze()
        self.assertFalse(any(i['type'] == 'BLIND_INTERCEPTOR' for i in issues))

    def test_temporal_lifecycle_lock(self):
        code = """
        function renderApp() {
            console.log('Rendering...');
        }
        function initApp() {
            console.log('Initializing...');
        }

        renderApp(); // Race condition: render before init
        initApp();
        """
        graph = SAPQCascadeGraph(code=code)
        issues = graph.analyze()
        self.assertTrue(any(i['type'] == 'TEMPORAL_LIFECYCLE_LOCK' for i in issues))

    def test_safe_temporal_lifecycle(self):
        code = """
        function renderApp() {
            console.log('Rendering...');
        }
        function initApp() {
            console.log('Initializing...');
        }

        initApp();
        renderApp(); // Safe: render after init
        """
        graph = SAPQCascadeGraph(code=code)
        issues = graph.analyze()
        self.assertFalse(any(i['type'] == 'TEMPORAL_LIFECYCLE_LOCK' for i in issues))

if __name__ == '__main__':
    unittest.main()
