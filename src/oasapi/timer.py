import logging
import time

log_timer = logging.getLogger(f"{__name__}.timer")


class Timer:
    def __init__(self, name="anonymous code block"):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        # log_timer.info(f"'{self.name}' started")
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.interval = self.end - self.start
        log_timer.info(f"'{self.name}' ran in {self.interval:.2f} seconds")
