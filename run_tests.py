import traceback
import unittest
from unittest import TestCase
import os

from pdip.utils import ModuleFinder

if __name__ == "__main__":
    def find_test_modules(root_directory):
        module_finder = ModuleFinder(root_directory=root_directory)
        module_finder.find_all_modules(folder='tests')
        test_modules = []
        for module in module_finder.modules:
            if module["module_name"].startswith('test_') and module["module_address"].startswith('tests'):
                test_modules.append(module)
        return test_modules


    def run_all_tests(test_modules):
        results = []
        for t in test_modules:
            suite = unittest.TestSuite()
            try:
                # If the module defines a suite() function, call it to get the suite.
                mod = __import__(t["module_address"], globals(), locals(), ['suite'])
                module = None
                for c in TestCase.__subclasses__():
                    if c.__module__.startswith(t["module_address"]):
                        module = c
                if module is not None:
                    # suitefn = getattr(module, 'suite')
                    suite.addTest(unittest.makeSuite(module))
            except (ImportError, AttributeError) as ex:
                # else, just load all the test cases from the module.
                trace = traceback.format_exc()
                print(trace)
                suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t["module_name"]))
            header_string = f'{"Case":75}|{"Runs".center(10)}|{"Success".center(10)}|{"Errors".center(10)}|{"Failures".center(10)}'
            print(f"{t['module_address']} tests started".center(len(header_string)+2,'-'))

            test_result = unittest.TextTestRunner().run(suite)
            result = {"test_namespace": t["module_address"], "result": test_result}

            results.append(result)
            print_results(results=[result])
            print(f"{t['module_address']} tests finished".center(len(header_string)+2,'-'))
            print("-" * (len(header_string)+2))
        return results


    def print_results(results):
        header_string = f'|{"Case":75}|{"Runs".center(10)}|{"Success".center(10)}|{"Errors".center(10)}|{"Failures".center(10)}|'
        print("-" * len(header_string))
        print(header_string)
        print("-" * len(header_string))
        total = {
            "runs": 0,
            "successes": 0,
            "errors": 0,
            "failures": 0,
        }
        for result in results:
            runs = result["result"].testsRun
            errors = len(result["result"].errors)
            failures = len(result["result"].failures)
            successes = runs - errors - failures

            total["runs"] += runs
            total["successes"] += successes
            total["errors"] += errors
            total["failures"] += failures
            result_string = f'|{result["test_namespace"]:75}|{runs:10}|{successes:10}|{errors:10}|{failures:10}|'
            print(result_string)
        total_string = f'|{"Total":75}|{total["runs"]:10}|{total["successes"]:10}|{total["errors"]:10}|{total["failures"]:10}|'
        print(total_string)
        print("-" * len(header_string))


    root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
    all_test_modules = find_test_modules(root_directory)
    test_results = run_all_tests(all_test_modules)
    print_results(test_results)
