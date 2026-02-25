"""
pipeline_logger.py — Structured pipeline trace logging.

Logs every step: User query → Retrieval → LLM call → Adaptive update → XP update → Response.
"""

import logging
import time
import functools

# Configure pipeline logger
logger = logging.getLogger("pipeline")

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [PIPELINE] %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class PipelineTrace:
    """Context manager for tracing a complete pipeline execution."""

    def __init__(self, name: str, **context):
        self.name = name
        self.context = context
        self.start_time = None
        self.steps = []

    def __enter__(self):
        self.start_time = time.time()
        ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        logger.info(f"▶ START {self.name} | {ctx_str}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        if exc_type:
            logger.error(f"✖ FAILED {self.name} after {elapsed:.2f}s | Error: {exc_val}")
            # Don't swallow — let it propagate
            return False
        else:
            logger.info(f"✔ DONE {self.name} in {elapsed:.2f}s | Steps: {len(self.steps)}")
        return False

    def log_step(self, step_name: str, details: str = ""):
        elapsed = time.time() - self.start_time
        self.steps.append(step_name)
        logger.info(f"  ├─ [{elapsed:.2f}s] {step_name}: {details}")


def traced(name: str):
    """Decorator to auto-trace a function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with PipelineTrace(f"{name}.{func.__name__}"):
                return func(*args, **kwargs)
        return wrapper
    return decorator
