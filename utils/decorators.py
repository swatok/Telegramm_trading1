import functools
import time
from typing import Callable, Any
from .logger import get_logger

logger = get_logger("decorators")

def log_execution(func: Callable) -> Callable:
    """Декоратор для логування виконання функції"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Executing {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Successfully executed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

def measure_time(func: Callable) -> Callable:
    """Декоратор для вимірювання часу виконання функції"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper

def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """Декоратор для повторних спроб виконання функції при помилці"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempts} failed: {str(e)}. Retrying...")
                    time.sleep(delay)
        return wrapper
    return decorator

def singleton(cls: Any) -> Any:
    """Декоратор для створення класів-синглтонів"""
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance
