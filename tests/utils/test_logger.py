from dialogy.utils.logger import debug, log


def test_debug_logs_on_function():
    def func(debug=True):
        return 4

    restrict_log_level = debug(log)(func)
    assert restrict_log_level(debug=True) == 4


def test_debug_logs_on_method():
    class Mock:
        def __init__(self, debug=False):
            self.debug = debug

        @debug(log)
        def func(self):
            return 4

    mock = Mock()
    assert mock.func() == 4


def test_debug_logs_on_method_missing_debug():
    class Mock:
        @debug(log)
        def func(self):
            return 4

    mock = Mock()
    assert mock.func() == 4


def test_debug_logs_dont_eat_docstrings():
    class Mock:
        @debug(log)
        def func(self):
            """lorem ipsum"""
            return 4

    mock = Mock()
    mock.func().__doc__ == "lorem ipsum"
