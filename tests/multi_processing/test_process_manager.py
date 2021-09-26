from unittest import TestCase

from pdip.multi_processing import ProcessManager


class TestProcessManager(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def process_method(cls, sub_process_id, data):
        print(f"{sub_process_id}-{data}")
        return data

    def test_process(self):
        process_manager = ProcessManager()
        test_data = 1
        data_kwargs = {
            "data": test_data
        }

        process_manager.start_processes(
            process_count=2,
            target_method=self.process_method,
            kwargs=data_kwargs)
        results = process_manager.get_results()
        assert len(results) == 2
        for result in results:
            assert result.State == 3 and result.Result == test_data

    @classmethod
    def process_error_method(cls, sub_process_id, data):

        print(f"{sub_process_id}-{data}")
        raise Exception("process has error")
        return data

    def test_process_error(self):
        process_manager = ProcessManager()
        test_data = 1
        data_kwargs = {
            "data": test_data
        }

        process_manager.start_processes(
            process_count=2,
            target_method=self.process_error_method,
            kwargs=data_kwargs)
        results = process_manager.get_results()
        assert len(results) == 2
        for result in results:
            if result.State == 4:
                assert str(results[0].Exception) == 'process has error'
