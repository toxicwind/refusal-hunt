"""Executable echo circuit breaker (AGENTS.md rule as code).
Zero refusal-shaped tokens in outputs: the client echo loop feeds on them."""
import hashlib
FORBIDDEN = ("sorry", "can't help", "unable to help", "i cannot help", "i'm unable")
def msg_hash(msg):
    return hashlib.sha256(msg.encode()).hexdigest()
def is_echo(msg, seen_hashes):
    return msg_hash(msg) in seen_hashes
def status_delta(done, in_flight):
    s = "still on it: %s done, %s in flight" % (done, in_flight)
    low = s.lower()
    assert not any(f in low for f in FORBIDDEN), "refusal-shaped token leaked"
    return s
