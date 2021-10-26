from os import path
from pdip.utils import ModuleFinder
from pdip.logging.loggers.console import ConsoleLogger
from traceback import format_exc
from unittest import TestCase
from unittest.loader import defaultTestLoader, makeSuite
from unittest.runner import TextTestRunner
from unittest.suite import TestSuite

if __name__ == "__main__":
    class TestRunner:
        def __init__(self):
            self.root_directory = path.abspath(path.join(path.dirname(path.abspath(__file__))))
            self.logger=ConsoleLogger()

        def run(self):
            all_test_modules = self.find_test_modules()
            test_results = self.run_all_tests(all_test_modules)
            self.print_results(test_results)

        def find_test_modules(self):
            module_finder = ModuleFinder(root_directory=self.root_directory)
            module_finder.find_all_modules(folder='tests')
            test_modules = []
            for module in module_finder.modules:
                if module["module_name"].startswith('test_') and module["module_address"].startswith('tests'):
                    test_modules.append(module)
            return test_modules


        def run_all_tests(self,test_modules):
            results = []
            for t in test_modules:
                suite = TestSuite()
                try:
                    # If the module defines a suite() function, call it to get the suite.
                    mod = __import__(t["module_address"], globals(), locals(), ['suite'])
                    module = None
                    for c in TestCase.__subclasses__():
                        if c.__module__.startswith(t["module_address"]):
                            module = c
                    if module is not None:
                        # suitefn = getattr(module, 'suite')
                        suite.addTest(makeSuite(module))
                except (ImportError, AttributeError) as ex:
                    # else, just load all the test cases from the module.
                    trace = format_exc()
                    self.logger.debug(trace)
                    suite.addTest(defaultTestLoader.loadTestsFromName(t["module_name"]))
                header_string = f'{"Case":75}|{"Runs".center(10)}|{"Success".center(10)}|{"Errors".center(10)}|{"Failures".center(10)}'
                self.logger.debug(f"{t['module_address']} tests started".center(len(header_string)+2,'-'))

                test_result = TextTestRunner().run(suite)
                result = {"test_namespace": t["module_address"], "result": test_result}

                results.append(result)
                self.print_results(results=[result])
                self.logger.debug(f"{t['module_address']} tests finished".center(len(header_string)+2,'-'))
                self.logger.debug("-" * (len(header_string)+2))
            return results


        def print_results(self,results):
            header_string = f'|{"Case":75}|{"Runs".center(10)}|{"Success".center(10)}|{"Errors".center(10)}|{"Failures".center(10)}|'
            self.logger.debug("-" * len(header_string))
            self.logger.debug(header_string)
            self.logger.debug("-" * len(header_string))
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
                self.logger.debug(result_string)
            total_string = f'|{"Total":75}|{total["runs"]:10}|{total["successes"]:10}|{total["errors"]:10}|{total["failures"]:10}|'
            self.logger.debug(total_string)
            self.logger.debug("-" * len(header_string))

    TestRunner().run()
