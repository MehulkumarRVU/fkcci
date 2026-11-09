#!/usr/bin/env python3
"""Run synthetic authenticated API workflows against an explicitly supplied test deployment."""

import argparse
import concurrent.futures
import json
import math
import os
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


PASSWORD = "SyntheticLoadTest-Only-Password-27!"


def request(
    base_url,
    path,
    method="GET",
    token=None,
    body=None,
    form=None,
    timeout_seconds=30,
):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    else:
        data = None
    req = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=data,
        headers=headers,
        method=method,
    )
    started = time.perf_counter()
    error_kind = None
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            response_body = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        response_body = error.read()
        status = error.code
    except (TimeoutError, socket.timeout):
        response_body = b""
        status = 0
        error_kind = "timeout"
    except urllib.error.URLError as error:
        response_body = b""
        status = 0
        error_kind = (
            "timeout"
            if isinstance(error.reason, (TimeoutError, socket.timeout))
            else "transport"
        )
    except OSError:
        response_body = b""
        status = 0
        error_kind = "transport"
    elapsed_ms = (time.perf_counter() - started) * 1000
    try:
        parsed = json.loads(response_body) if response_body else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        parsed = None
    return status, elapsed_ms, parsed, error_kind


def run_user(base_url, profile, index):
    suffix = uuid.uuid4().hex[:12]
    username = f"loadtest_{profile}_{index}_{suffix}"
    email = f"{username}@example.com"
    records = []

    def call(path, **kwargs):
        status, latency, data, error_kind = request(base_url, path, **kwargs)
        records.append({
            "path": path,
            "status": status,
            "latency_ms": latency,
            "error_kind": error_kind,
        })
        return status, data

    status, _ = call(
        "/api/auth/signup",
        method="POST",
        body={
            "email": email,
            "username": username,
            "password": PASSWORD,
            "sport_type": "boxing",
        },
    )
    if status != 201:
        return records

    status, data = call(
        "/api/auth/login",
        method="POST",
        form={"username": username, "password": PASSWORD},
    )
    if status != 200 or not data:
        return records
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not access_token or not refresh_token:
        return records

    call("/api/auth/me", token=access_token)
    call("/api/adaptive/profile", token=access_token)
    call("/api/adaptive/catalog?category=boxing")
    call("/api/skills/", token=access_token)
    status, session = call(
        "/api/sessions/",
        method="POST",
        token=access_token,
        body={"sport_type": "boxing", "session_type": "drill", "skill_name": "Jab"},
    )
    call("/api/sessions/", token=access_token)
    call("/api/analytics/me/profile-twin", token=access_token)
    if status == 201 and session:
        landmarks = [
            {"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.9}
            for _ in range(33)
        ]
        call(
            "/api/analysis/analyze",
            method="POST",
            token=access_token,
            body={
                "sport_type": "boxing",
                "skill_name": "Jab",
                "session_id": session["id"],
                "pose_data": [{"landmarks": landmarks, "timestamp": time.time()}],
            },
        )

    status, refreshed = call(
        "/api/auth/token/refresh",
        method="POST",
        body={"refresh_token": refresh_token},
    )
    if status == 200 and refreshed:
        access_token = refreshed.get("access_token")
        refresh_token = refreshed.get("refresh_token")
    call(
        "/api/auth/logout",
        method="POST",
        body={"refresh_token": refresh_token},
    )
    return records


def nearest_rank(values, percentile):
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(percentile * len(ordered)) - 1)], 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("LOAD_TEST_BASE_URL"))
    parser.add_argument(
        "--concurrency",
        default="10,25,50,100",
        help="comma-separated synthetic user counts (e.g. 10,25,50,100)",
    )
    parser.add_argument(
        "--cooldown-seconds",
        type=float,
        default=1.0,
        help="pause between load profiles",
    )
    parser.add_argument(
        "--probe-interval-seconds",
        type=float,
        default=0,
        help="optional interval for concurrent backend responsiveness probes",
    )
    args = parser.parse_args()
    if not args.base_url:
        parser.error("--base-url or LOAD_TEST_BASE_URL is required")

    warmup_statuses = {}
    for _ in range(10):
        status, _, _, _ = request(args.base_url, "/health/ready")
        key = str(status)
        warmup_statuses[key] = warmup_statuses.get(key, 0) + 1

    reports = []
    for level in (int(value) for value in args.concurrency.split(",")):
        probe_records = []
        stop_probes = threading.Event()

        def probe_health():
            while not stop_probes.is_set():
                status, latency, _, error_kind = request(
                    args.base_url,
                    "/api/adaptive/capabilities",
                    timeout_seconds=2,
                )
                probe_records.append({
                    "status": status,
                    "latency_ms": latency,
                    "error_kind": error_kind,
                })
                stop_probes.wait(args.probe_interval_seconds)

        probe_thread = None
        if args.probe_interval_seconds > 0:
            probe_thread = threading.Thread(target=probe_health, daemon=True)
            probe_thread.start()

        started = time.perf_counter()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=level) as pool:
                groups = list(
                    pool.map(
                        lambda index: run_user(args.base_url, level, index),
                        range(level),
                    )
                )
        finally:
            stop_probes.set()
            if probe_thread is not None:
                probe_thread.join(timeout=3)
        elapsed = time.perf_counter() - started
        records = [record for group in groups for record in group]
        latencies = [record["latency_ms"] for record in records]
        statuses = {}
        for record in records:
            key = str(record["status"])
            statuses[key] = statuses.get(key, 0) + 1
        http_errors = sum(record["status"] >= 400 for record in records)
        timeouts = sum(record["error_kind"] == "timeout" for record in records)
        transport_errors = sum(record["error_kind"] == "transport" for record in records)
        failures = sum(
            record["status"] < 200
            or record["status"] >= 400
            or record["error_kind"] is not None
            for record in records
        )
        endpoint_breakdown = {}
        for path in sorted({record["path"] for record in records}):
            endpoint_records = [record for record in records if record["path"] == path]
            endpoint_latencies = [record["latency_ms"] for record in endpoint_records]
            endpoint_failures = sum(
                record["status"] < 200 or record["status"] >= 400
                for record in endpoint_records
            )
            endpoint_breakdown[path] = {
                "requests": len(endpoint_records),
                "p50_ms": nearest_rank(endpoint_latencies, 0.50),
                "p95_ms": nearest_rank(endpoint_latencies, 0.95),
                "max_ms": round(max(endpoint_latencies), 2),
                "errors": endpoint_failures,
            }
        reports.append(
            {
                "users": level,
                "requests": len(records),
                "elapsed_seconds": round(elapsed, 3),
                "throughput_rps": round(len(records) / elapsed, 2) if elapsed else 0,
                "latency_ms": {
                    "p50": nearest_rank(latencies, 0.50) if latencies else None,
                    "p95": nearest_rank(latencies, 0.95) if latencies else None,
                    "p99": nearest_rank(latencies, 0.99) if latencies else None,
                    "max": round(max(latencies), 2) if latencies else None,
                },
                "status_counts": statuses,
                "http_errors": http_errors,
                "timeouts": timeouts,
                "transport_errors": transport_errors,
                "error_percentage": round(100 * failures / len(records), 2) if records else 100,
                "backend_responsiveness_probe": {
                    "requests": len(probe_records),
                    "p50_ms": nearest_rank(
                        [record["latency_ms"] for record in probe_records], 0.50
                    ) if probe_records else None,
                    "p95_ms": nearest_rank(
                        [record["latency_ms"] for record in probe_records], 0.95
                    ) if probe_records else None,
                    "p99_ms": nearest_rank(
                        [record["latency_ms"] for record in probe_records], 0.99
                    ) if probe_records else None,
                    "errors": sum(
                        record["status"] != 200 or record["error_kind"] is not None
                        for record in probe_records
                    ),
                },
                "endpoint_breakdown": endpoint_breakdown,
                "synthetic_accounts_created": sum(
                    1 for record in records
                    if record["path"] == "/api/auth/signup" and record["status"] == 201
                ),
            }
        )
        time.sleep(max(0, args.cooldown_seconds))

    print(
        json.dumps(
            {
                "base_url": args.base_url,
                "warmup_requests": 10,
                "warmup_status_counts": warmup_statuses,
                "profiles": reports,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
