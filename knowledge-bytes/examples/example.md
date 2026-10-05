# Worked Example: Retry with Backoff

This example shows the [Knowledge Bytes prompt](../knowledge-bytes-prompt.md)
applied to a small, realistic Python helper: `fetch_with_retry`, which calls a
network function and retries transient failures with exponential backoff. It is
the kind of function you meet constantly in unfamiliar codebases and rarely get
a proper explanation of.

The code being explained:

```python
import random
import time


def fetch_with_retry(url, fetch, max_attempts=4, base_delay=0.5):
    """Call fetch(url), retrying transient network failures.

    Waits progressively longer between attempts (exponential backoff
    with jitter) and re-raises the last error if all attempts fail.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fetch(url)
        except (TimeoutError, ConnectionError) as e:
            last_error = e
            if attempt == max_attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            delay = delay * random.uniform(0.8, 1.2)
            time.sleep(delay)
    raise last_error
```

---

```text
BYTE 1: The contract — what this function promises
Builds on: nothing — this is the starting point
In plain terms: This function tries to fetch something over the network, and
if the network flakes out, it waits a bit and tries again instead of giving
up immediately.
The code:
    def fetch_with_retry(url, fetch, max_attempts=4, base_delay=0.5):
        """Call fetch(url), retrying transient network failures.

        Waits progressively longer between attempts (exponential backoff
        with jitter) and re-raises the last error if all attempts fail.
        """
What's happening: The signature tells the whole deal up front: give it a URL,
a fetch function to call, how many total attempts to allow (4), and how long
to wait before the first retry (0.5 seconds). The docstring states the two
guarantees: retries wait progressively longer, and if everything fails, the
original error is re-raised rather than swallowed.
Why it matters: Networks fail transiently all the time — a single dropped
packet should not crash a program. This function is the codebase's standard
answer to "what do we do when a request fails," so understanding its contract
tells you what every caller of it can assume.
```

```text
BYTE 2: The retry loop — the structural skeleton
Builds on: Byte 1
In plain terms: Try the fetch; if it works, return the result immediately. If
a network error occurs, remember it and either wait and retry or give up.
The code:
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fetch(url)
        except (TimeoutError, ConnectionError) as e:
            last_error = e
            if attempt == max_attempts:
                break
            ...
    raise last_error
What's happening: The loop runs at most max_attempts times. Each iteration
tries fetch(url) and returns its result on success — so a first-try success
never touches any retry logic. Only TimeoutError and ConnectionError are
caught; anything else propagates immediately. The caught error is saved, and
if this was the final attempt the loop breaks; otherwise execution falls
through to the waiting logic (Byte 3). If the loop ends without a return, the
last saved error is raised.
Why it matters: This is the control flow every other byte hangs on. Note the
deliberate narrowness of the except clause: the function distinguishes
"the network glitched, try again" from "something is actually wrong," which is
the difference between resilience and hiding bugs.
```

```text
BYTE 3: The waiting math — exponential backoff with jitter
Builds on: Bytes 1, 2
In plain terms: Each retry waits roughly twice as long as the previous one,
with a small random wobble so that many clients retrying at once don't all
hammer the server in lockstep.
The code:
    delay = base_delay * (2 ** (attempt - 1))
    delay = delay * random.uniform(0.8, 1.2)
    time.sleep(delay)
What's happening: On attempt 1 the delay is base_delay * 1 (0.5s by default),
on attempt 2 it is base_delay * 2, then * 4 — doubling each time. That
computed delay is then multiplied by a random factor between 0.8 and 1.2, so
the actual wait varies slightly around the target. time.sleep pauses the
program for that long before the next loop iteration retries.
Why it matters: Fixed-interval retries can synchronize across clients and
overwhelm a recovering server (the "thundering herd"); exponential growth
gives the server breathing room, and jitter breaks the synchronization. These
three lines are the entire reason this helper is preferable to a naive
"try three times" loop.
```

```text
BYTE 4: Gotchas — what can surprise you
Builds on: Bytes 1–3
In plain terms: This helper only retries two specific error types, it blocks
the whole thread while waiting, and when it finally gives up it raises the
last network error, not a custom "retries exhausted" error.
The code:
    except (TimeoutError, ConnectionError) as e:
    ...
    time.sleep(delay)
    ...
    raise last_error
What's happening: A ValueError, an HTTP 404 surfaced as an exception, or any
non-network error is never retried — it propagates on the first attempt,
which is correct (retrying a permanent failure is pointless) but easy to
misread as "retries everything." time.sleep blocks the calling thread, so in asynchronous or event-driven
code this helper would stall execution; it is designed for
simple synchronous scripts. Finally, exhaustion raises the raw last_error —
callers checking for a specific "gave up" signal must count on the exception
type from fetch, not on anything this function adds.
Why it matters: These are the details that cause real bugs: wrapping this in
an async task, expecting it to retry a 500-error wrapper exception, or trying
to catch a distinctive "out of retries" exception that does not exist. Edge
cases last, but they are what separate using the helper from understanding it.
```

```text
PUTTING IT TOGETHER
fetch_with_retry is a small resilience wrapper with a simple deal (Byte 1):
give it a fetch function and it will keep trying through transient network
failures. Its skeleton is a bounded try/except loop that returns on first
success and re-raises the last error on exhaustion (Byte 2); between attempts
it waits with exponential backoff plus jitter to avoid hammering a struggling
server (Byte 3). It is deliberately narrow — only TimeoutError and
ConnectionError are retried, it blocks while sleeping, and it adds no custom
exception of its own (Byte 4). Mental model: "try up to N times, wait
increasingly long and slightly random intervals between tries, retry only
network glitches, and hand me the real error if nothing worked."
```
