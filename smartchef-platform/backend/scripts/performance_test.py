#!/usr/bin/env python3
"""
性能测试脚本：采集指令 API 延迟、可选准确率与 QPS。

用法（需后端已启动且已发布版本）：
  python -m scripts.performance_test
  python -m scripts.performance_test --base-url http://localhost:8000 --samples 50
  python -m scripts.performance_test --p95-threshold 200 --warmup 3

输出：P50/P95/P99 延迟（ms）、样本数、是否通过 SC-002 阈值（默认 200ms）。
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
import uuid

try:
    import httpx
except ImportError:
    print("pip install httpx", file=sys.stderr)
    sys.exit(1)

DEFAULT_BASE = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
DEFAULT_SAMPLES = 50
DEFAULT_WARMUP = 3
SC002_P95_MS = 200


def main():
    p = argparse.ArgumentParser(description="SmartChef 指令 API 性能采样")
    p.add_argument("--base-url", default=DEFAULT_BASE, help="后端 base URL")
    p.add_argument("--samples", type=int, default=DEFAULT_SAMPLES, help="采样次数")
    p.add_argument("--warmup", type=int, default=DEFAULT_WARMUP, help="预热次数（不计入统计）")
    p.add_argument("--reuse-device-id", action="store_true", help="复用同一 device_id（默认每次请求使用新 device_id）")
    p.add_argument("--interval-ms", type=float, default=120.0, help="请求间隔（毫秒），用于避免触发限流")
    p.add_argument("--p95-threshold", type=float, default=SC002_P95_MS, help="P95 延迟阈值(ms)")
    args = p.parse_args()

    url = f"{args.base_url.rstrip('/')}{API_PREFIX}/dialog/chat"
    payload_base = {
        "text": "设置温度180度",
        "language": "zh",
    }

    latencies_ms: list[float] = []
    errors = 0
    first_error_status: int | None = None
    first_error_body: str = ""

    print(
        f"Target: {url} | warmup={args.warmup} | samples={args.samples} | "
        f"reuse_device_id={args.reuse_device_id} | interval_ms={args.interval_ms} | P95 threshold={args.p95_threshold}ms"
    )

    with httpx.Client(timeout=10.0) as client:
        print("Warmup ...")
        for i in range(max(args.warmup, 0)):
            warm_payload = {
                **payload_base,
                "device_id": f"perf-warmup-{uuid.uuid4().hex[:8]}-{i}",
            }
            try:
                client.post(url, json=warm_payload)
            except Exception:
                pass

        print("Sampling ...")
        fixed_device_id = f"perf-test-fixed-{uuid.uuid4().hex[:8]}"

        for i in range(args.samples):
            device_id = fixed_device_id if args.reuse_device_id else f"perf-test-{uuid.uuid4().hex[:8]}-{i}"
            payload = {**payload_base, "device_id": device_id}

            t0 = time.perf_counter()
            try:
                r = client.post(url, json=payload)
                if r.status_code != 200:
                    if first_error_status is None:
                        first_error_status = r.status_code
                        first_error_body = r.text[:500] if r.text else ""
                    errors += 1
                else:
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    latencies_ms.append(elapsed_ms)
            except Exception as e:
                if first_error_status is None:
                    first_error_body = str(e)
                    first_error_status = 0
                errors += 1

            if args.interval_ms > 0:
                time.sleep(args.interval_ms / 1000.0)

    if not latencies_ms:
        print("No successful samples; check backend and version.")
        if first_error_status is not None:
            print(f"  First error: HTTP {first_error_status}")
            if first_error_body:
                print(f"  Body: {first_error_body[:300]}")
        print("  Tip: ensure a dialog version is published (e.g. from Versions page).")
        sys.exit(1)

    n = len(latencies_ms)
    sorted_ms = sorted(latencies_ms)
    p50 = sorted_ms[int(n * 0.50)]
    p95 = sorted_ms[min(int(n * 0.95), n - 1)]
    p99 = sorted_ms[min(int(n * 0.99), n - 1)]
    avg = statistics.mean(latencies_ms)

    print("\n--- Result ---")
    print(f"  Samples: {n} ok, {errors} fail")
    if errors > 0 and first_error_status is not None:
        print(f"  First error: HTTP {first_error_status}")
        if first_error_body:
            print(f"  Body: {first_error_body[:120]}")
    print(f"  Avg:     {avg:.1f} ms")
    print(f"  P50:     {p50:.1f} ms")
    print(f"  P95:     {p95:.1f} ms")
    print(f"  P99:     {p99:.1f} ms")
    print(f"  SC-002 (P95 < {args.p95_threshold}ms): {'PASS' if p95 < args.p95_threshold else 'FAIL'}")

    if p95 >= args.p95_threshold:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
