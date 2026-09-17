"""utime: microsecond-resolution timing for everything. Chris's rule: time everything at us level."""
import time, json, os

TIMING_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timings.jsonl")

def now_us() -> int:
    return time.perf_counter_ns() // 1000

def now_wall_us() -> int:
    return time.time_ns() // 1000

class span:
    """with utime.span("parquet_write", detail="spawns.parquet"): ...  -> logs us elapsed to timings.jsonl"""
    def __init__(self, name, detail="", log_path=None):
        self.name = name
        self.detail = detail
        self.log_path = log_path or TIMING_LOG
    def __enter__(self):
        self.t0 = now_us()
        return self
    def __exit__(self, *exc):
        self.t1 = now_us()
        rec = {"t0_us": self.t0, "t1_us": self.t1, "elapsed_us": self.t1 - self.t0,
               "op": self.name, "detail": self.detail,
               "wall_us": now_wall_us()}
        with open(self.log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return False

def log_event(op, detail="", elapsed_us=None, extra=None):
    rec = {"op": op, "detail": detail, "wall_us": now_wall_us()}
    if elapsed_us is not None:
        rec["elapsed_us"] = elapsed_us
    if extra:
        rec.update(extra)
    with open(TIMING_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
