import unittest
import os
from modules.sapq.sapq_baseline_cube import SAPQBaselineCube

class TestSAPQBaselineCube(unittest.TestCase):
    def test_semantic_role_preservation(self):
        # Baseline code has a function that reads state and mutates the DOM.
        baseline_code = """
        const appState = { theme: 'dark' };
        function applyTheme() {
            document.getElementById('body').className = appState.theme;
        }
        """

        # Target code renamed the function and variables, but the topological role remains identical.
        target_code = """
        const myStore = { colorMode: 'dark' };
        function updateColorMode() {
            document.getElementById('body').className = myStore.colorMode;
        }
        """
        cube = SAPQBaselineCube(baseline_filepath="fake_base.js", target_filepath="fake_target.js",
                                baseline_code=baseline_code, target_code=target_code)

        issues = cube.audit_topological_holes()
        # Because the topological role (READS_STATE:True|WRITES_DOM:True|IS_HANDLER:False) is identical,
        # there should be no topological holes detected despite the complete rewrite.
        self.assertEqual(len(issues), 0)

    def test_missing_intended_feature(self):
        # Baseline has two functions. One handles an event and writes to the DOM.
        baseline_code = """
        function onClickToggle() {
            document.getElementById('dropdown').style.display = 'none';
        }
        """

        # Target code completely omitted this logic (Silent Stubbing).
        target_code = """
        function someOtherFunction() {
            console.log('Doing nothing');
        }
        """

        cube = SAPQBaselineCube(baseline_filepath="fake_base.js", target_filepath="fake_target.js",
                                baseline_code=baseline_code, target_code=target_code)

        issues = cube.audit_topological_holes()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['type'], "MISSING_INTENDED_FEATURE")
        self.assertTrue('onClickToggle' in issues[0]['original_functions'])

if __name__ == '__main__':
    unittest.main()
