import logging
import sys

logger = logging.getLogger(__name__)


class CometValidationError(Exception):
    pass


class CometCallsTracer(object):
    """
    Debug context manager to trace any function calls inside the context

    Reference:
        https://stackoverflow.com/questions/32163436/python-decorator-for-printing-every-line-executed-by-a-function
        (Thanks to the handy implementation by 'https://stackoverflow.com/users/3646530/ashwinjv)
    """

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        logger.debug('Entering Debug Decorated func')
        # Set the trace function to the trace_calls function
        # So all events are now traced
        sys.settrace(self.trace_calls)

    def __exit__(self, *args, **kwargs):
        # Stop tracing all events
        sys.settrace = None

    def trace_calls(self, frame, event, arg):
        # We want to only trace our call to the decorated function
        if event != 'call':
            return
        elif frame.f_code.co_name != self.name:
            return
        # return the trace function to use when you go into that
        # function call
        return self.trace_lines

    def trace_lines(self, frame, event, arg):
        # If you want to print local variables each line
        # keep the check for the event 'line'
        # If you want to print local variables only on return
        # check only for the 'return' event
        if (event not in ['line', 'return']) or (event == "line" and not self.trace_lines):
            return
        co = frame.f_code
        func_name = co.co_name
        line_no = frame.f_lineno
        filename = co.co_filename
        local_vars = frame.f_locals
        logger.debug(f"Function/method: {func_name}, Event type: {event} Line no.: {line_no} locals: {local_vars}")


class CometDeprecationContext(object):
    """
    Context manager to mark the deprecated any function calls inside the context

    Reference:
        https://stackoverflow.com/questions/32163436/python-decorator-for-printing-every-line-executed-by-a-function
        (Thanks to the handy implementation by 'https://stackoverflow.com/users/3646530/ashwinjv)
    """

    def __init__(self, reason):
        self.reason = reason

    def __enter__(self):
        logger.debug(f"Executing additional lines of code to support the deprecated functionalities")

    def __exit__(self, *args, **kwargs):
        logger.debug(f"End of additional lines of code to support the deprecated functionalities")

class CometUtilities(object):

    @staticmethod
    def trace_function_calls(func):
        """ Debug decorator to call the function within the debug context """
        def wrapper(*args, **kwargs):
            with CometCallsTracer(func.__name__):
                return_value = func(*args, **kwargs)
            return return_value
        return wrapper

    @staticmethod
    def unsupported_function_error(func) -> None:
        def wrapper(*args, **kwargs):
            raise Exception(f"Unsupported function/method '{func.__qualname__}' is executed!")
        return wrapper

    @staticmethod
    def unstable_function_warning(func) -> None:
        def wrapper(*args, **kwargs):
            logger.warning(f"Unstable function/method '{func.__qualname__}' is executed!")
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def deprecated_function_warning(func) -> None:
        def wrapper(*args, **kwargs):
            logger.warning(f"Deprecated function/method '{func.__qualname__}' is executed!")
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def deprecation_utility_lines() -> None:
        logger.warning(f"Additional line/s to support deprecated features/logic is/are executed")

    @staticmethod
    def deprecation_facilitation_warning(func) -> None:
        def wrapper(*args, **kwargs):
            logger.warning(f"Function/Method '{func.__qualname__}' to support deprecated features/logic is executed")
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def deprecated_arguments_warning(*removed_params, **replaced_params) -> None:
        def wrapper_1(func):
            def wrapper_2(*args, **kwargs):
                for param in removed_params:
                    if param in args or (param in kwargs and kwargs[param] not in [None, ""]):
                        logger.warning(
                            f"Deprecated argument '{param}' is provided in '{func.__qualname__}' "
                            f"method/function"
                        )
                for param in replaced_params:
                    if param in args or param in kwargs:
                        logger.warning(
                            f"Deprecated argument '{param}' that is replaced by '{replaced_params[param]}' "
                            f"is provided and '{func.__qualname__}' method/function"
                        )
                return func(*args, **kwargs)
            return wrapper_2
        return wrapper_1
