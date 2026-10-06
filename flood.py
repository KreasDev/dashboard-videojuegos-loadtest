#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import socket
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- Safety bounds (kept from the original script) ---
REPORT_INTERVAL_SECONDS = 3
MAX_DURATION_SECONDS = 300
MAX_CONCURRENCY = 500
MAX_REQUESTS_PER_SECOND = 500
MAX_TIMEOUT_SECONDS = 60          # added bound for the new --timeout argument

# --- Defaults (kept from the original script) ---
DEFAULT_DURATION = 20
DEFAULT_CONCURRENCY = 40
DEFAULT_REQUESTS_PER_SECOND = 50
DEFAULT_TIMEOUT_SECONDS = 2
DEFAULT_PATH = "/"


def positive_bounded(name: str, maximum: int):
    """argparse type: an integer in 1..maximum."""
    def _parse(raw: str) -> int:
        try:
            value = int(raw)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} must be an integer; got {raw!r}")
        if not 1 <= value <= maximum:
            raise argparse.ArgumentTypeError(
                f"{name} must be between 1 and {maximum}; got {value}"
            )
        return value
    return _parse


def port_type(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"port must be an integer; got {raw!r}")
    if not 1 <= value <= 65535:
        raise argparse.ArgumentTypeError(f"port must be between 1 and 65535; got {value}")
    return value


def assert_local_target(host: str) -> None:
    """Abort unless every resolved address is loopback or RFC1918 private.

    Lab-only safety: this cannot be disabled. localhost / 127.0.0.1 / ::1 and
    Docker-local private ranges (10/8, 172.16/12, 192.168/16) are allowed.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as error:
        raise SystemExit(f"Cannot resolve host {host!r}: {error}")

    addresses = {info[4][0] for info in infos}
    for addr in addresses:
        ip = ipaddress.ip_address(addr.split("%", 1)[0])  # strip IPv6 zone id
        if not (ip.is_loopback or ip.is_private):
            raise SystemExit(
                f"Refusing non-local target {host!r} -> {addr}. "
                "This lab tool only targets localhost/127.0.0.1/::1 or private "
                "(10/8, 172.16/12, 192.168/16) addresses."
            )


def request_status(opener: urllib.request.OpenerDirector, url: str, timeout: int) -> str:
    """Perform one GET and return its HTTP status, or 000 on network failure."""
    request = urllib.request.Request(url, method="GET")
    try:
        with opener.open(request, timeout=timeout) as response:
            return str(response.status)
    except urllib.error.HTTPError as error:
        return str(error.code)
    except (urllib.error.URLError, TimeoutError, OSError):
        return "000"


class RateLimiter:
    """Limit aggregate request starts across all workers for one target."""

    def __init__(self, requests_per_second: int) -> None:
        self.interval = 1 / requests_per_second
        self.next_request_at = 0.0
        self.lock = threading.Lock()

    def wait_for_turn(self, stop_event: threading.Event) -> bool:
        with self.lock:
            now = time.monotonic()
            scheduled_at = max(now, self.next_request_at)
            self.next_request_at = scheduled_at + self.interval
        return not stop_event.wait(max(0.0, scheduled_at - now))


def worker(
    url: str,
    timeout: int,
    deadline: float,
    stop_event: threading.Event,
    rate_limiter: RateLimiter,
    counts: Counter,
    counts_lock: threading.Lock,
) -> None:
    """Send requests until the fixed deadline or an interrupt."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while not stop_event.is_set() and time.monotonic() < deadline:
        if not rate_limiter.wait_for_turn(stop_event):
            break
        if time.monotonic() >= deadline:
            break
        code = request_status(opener, url, timeout)
        with counts_lock:
            counts[code] += 1


def snapshot(counts: Counter, counts_lock: threading.Lock) -> Counter:
    with counts_lock:
        return counts.copy()


def report(target: str, counts: Counter, final: bool = False) -> None:
    total = sum(counts.values())
    ok = counts["200"]
    failed = total - ok
    label = "RESULT" if final else f"[{datetime.now():%H:%M:%S}] requests so far"
    print(f"  {label} for {target}: total={total} ok(200)={ok} blocked/failed={failed}", flush=True)


def run_target(
    url: str,
    display: str,
    concurrency: int,
    duration: int,
    requests_per_second: int,
    timeout: int,
) -> None:
    counts: Counter = Counter()
    counts_lock = threading.Lock()
    stop_event = threading.Event()
    rate_limiter = RateLimiter(requests_per_second)
    started_at = time.monotonic()
    deadline = started_at + duration

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                worker, url, timeout, deadline, stop_event, rate_limiter, counts, counts_lock
            )
            for _ in range(concurrency)
        ]
        try:
            while time.monotonic() < deadline:
                time.sleep(min(REPORT_INTERVAL_SECONDS, deadline - time.monotonic()))
                report(display, snapshot(counts, counts_lock))
        except KeyboardInterrupt:
            stop_event.set()
            print("\nStopping workers after Ctrl-C...", flush=True)
        finally:
            stop_event.set()
        for future in futures:
            future.result()

    real_duration = time.monotonic() - started_at
    final = snapshot(counts, counts_lock)
    total = sum(final.values())
    ok = final["200"]
    failed = total - ok
    report(display, final, final=True)
    error_pct = (failed * 100 / total) if total else 0.0
    throughput = (total / real_duration) if real_duration else 0.0
    print("\n=== Summary ===", flush=True)
    print(f"  Target:            {display}")
    print(f"  Total requests:    {total}")
    print(f"  Successful (200):  {ok}")
    print(f"  Failed/blocked:    {failed}")
    print(f"  Error rate:        {error_pct:.1f}%")
    print(f"  Real duration:     {real_duration:.2f}s")
    print(f"  Throughput:        {throughput:.1f} req/s (approx)")
    print("\nA non-200 result can be a Fail2ban block, an HTTP error, or a timeout.")
    print("Only the configured local lab target was contacted.", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bounded HTTP load test for the LOCAL Fail2ban lab only.",
    )
    parser.add_argument("host", help="Target host (localhost/127.0.0.1/::1 or a private LAN/Docker IP)")
    parser.add_argument("port", type=port_type, help="Target TCP port (1-65535)")
    parser.add_argument("--path", default=DEFAULT_PATH, help=f"Request path (default: {DEFAULT_PATH})")
    parser.add_argument("--concurrency", type=positive_bounded("concurrency", MAX_CONCURRENCY),
                        default=DEFAULT_CONCURRENCY, help=f"Parallel workers (default: {DEFAULT_CONCURRENCY}, max {MAX_CONCURRENCY})")
    parser.add_argument("--rps", type=positive_bounded("rps", MAX_REQUESTS_PER_SECOND),
                        default=DEFAULT_REQUESTS_PER_SECOND, help=f"Aggregate request-start rate (default: {DEFAULT_REQUESTS_PER_SECOND}, max {MAX_REQUESTS_PER_SECOND})")
    parser.add_argument("--duration", type=positive_bounded("duration", MAX_DURATION_SECONDS),
                        default=DEFAULT_DURATION, help=f"Seconds to run (default: {DEFAULT_DURATION}, max {MAX_DURATION_SECONDS})")
    parser.add_argument("--timeout", type=positive_bounded("timeout", MAX_TIMEOUT_SECONDS),
                        default=DEFAULT_TIMEOUT_SECONDS, help=f"Per-request timeout seconds (default: {DEFAULT_TIMEOUT_SECONDS}, max {MAX_TIMEOUT_SECONDS})")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    assert_local_target(args.host)

    path = args.path if args.path.startswith("/") else f"/{args.path}"
    host_for_url = f"[{args.host}]" if ":" in args.host else args.host  # bracket IPv6
    url = f"http://{host_for_url}:{args.port}{path}"
    display = f"{args.host}:{args.port}{path}"

    print("=== Bounded HTTP lab test ===", flush=True)
    print(f"  Target:       {url}")
    print(f"  Concurrency:  {args.concurrency} workers")
    print(f"  RPS (max):    {args.rps} requests/s aggregate")
    print(f"  Duration:     {args.duration}s")
    print(f"  Timeout:      {args.timeout}s per request\n", flush=True)

    run_target(url, display, args.concurrency, args.duration, args.rps, args.timeout)


if __name__ == "__main__":
    main()
