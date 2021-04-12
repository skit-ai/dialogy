from dialogy.utils.logger import debug_logs


def test_debug_logs_on_function():
    def func(debug=True):
        return 4

    restrict_log_level = debug_logs(func)
    assert restrict_log_level(debug=True) == 4


def test_debug_logs_on_method():
    class Mock:
        def __init__(self, debug=False):
            self.debug = debug

        @debug_logs
        def func(self):
            return 4

    mock = Mock()
    assert mock.func() == 4


def test_debug_logs_on_method_missing_debug():
    class Mock:
        @debug_logs
        def func(self):
            return 4

    mock = Mock()
    assert mock.func() == 4
