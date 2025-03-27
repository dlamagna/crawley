import sys
from datetime import datetime, timezone

class DualLogger:
    def __init__(self, base_filename="log", verbose=False):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.verbose = verbose
        if self.verbose:
            self.terminal = sys.__stdout__
        self.log = open(f"{base_filename}_{timestamp}.log", "a", encoding="utf-8")

    def write(self, message):
        if self.verbose:
            self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        if self.verbose:
            self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()