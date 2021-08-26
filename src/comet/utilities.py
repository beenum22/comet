import logging

logger = logging.getLogger(__name__)


class CometValidationError(Exception):
    pass


class CometUtilities(object):

    @staticmethod
    def unsupported_function_error(func) -> None:
        def wrapper(*args, **kwargs):
            raise Exception(f"Unsupported function/method '{func.__name__}' is executed!")
        return wrapper

    @staticmethod
    def unstable_function_warning(func) -> None:
        def wrapper(*args, **kwargs):
            logger.warning(f"Unstable function/method '{func.__name__}' is executed!")
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def deprecated_function_warning(func) -> None:
        def wrapper(*args, **kwargs):
            logger.warning(f"Deprecated function/method '{func.__name__}' is executed!")
            return func(*args, **kwargs)
        return wrapper