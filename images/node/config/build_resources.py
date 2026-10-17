#!/usr/bin/env python3
"""Bound source-build workers by affinity, cgroup quotas and memory headroom.

Only capacity/counter data is reported: no environment, hostnames or addresses.
Compatible with the Python 3 supplied by the configured Linux builder.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import sys

GIB = 1024 ** 3
BUILD_RESERVE_BYTES = GIB // 2
WORKER_MEMORY_BYTES = 7 * GIB // 4


def read(path):
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return ""


def counters(path):
    result = {}
    for line in read(path).splitlines():
        fields = line.split()
        if len(fields) == 2:
            try:
                result[fields[0].rstrip(":")] = int(fields[1])
            except ValueError:
                pass
        elif len(fields) == 3 and fields[2] == "kB":
            result[fields[0].rstrip(":")] = int(fields[1]) * 1024
    return result


def unescape(value):
    for escaped, literal in (("\\040", " "), ("\\011", "\t"), ("\\134", "\\")):
        value = value.replace(escaped, literal)
    return value


def cgroup_directories(root):
    """Resolve current membership against mounts; include all visible ancestors."""
    memberships = {}
    for line in read(root / "proc/self/cgroup").splitlines():
        fields = line.split(":", 2)
        if len(fields) == 3:
            for controller in fields[1].split(","):
                memberships[controller] = fields[2]
    result = {"cpu": [], "memory": []}
    for line in read(root / "proc/self/mountinfo").splitlines():
        before, separator, after = line.partition(" - ")
        fields, tail = before.split(), after.split()
        if not separator or len(fields) < 5 or len(tail) < 3:
            continue
        kind = tail[0]
        if kind not in ("cgroup", "cgroup2"):
            continue
        mount_root, mount_path = unescape(fields[3]), unescape(fields[4])
        for controller in result:
            if kind == "cgroup" and controller not in tail[2].split(","):
                continue
            membership = memberships.get("" if kind == "cgroup2" else controller)
            if membership is None:
                continue
            if membership == "/":
                relative = ""  # private cgroup namespace: its root is the mount
            elif mount_root == "/":
                relative = membership.lstrip("/")
            elif membership == mount_root or membership.startswith(mount_root + "/"):
                relative = membership[len(mount_root):].lstrip("/")
            else:
                continue
            if ".." in Path(relative).parts:
                continue
            mount = root / mount_path.lstrip("/")
            current = mount / relative
            while True:
                result[controller].append((current, kind))
                if current == mount:
                    break
                current = current.parent
    return result


def collect(root=Path("/"), affinity=None):
    if affinity is None:
        affinity = len(os.sched_getaffinity(0))
    mem = counters(root / "proc/meminfo")
    total = mem.get("MemTotal", 0)
    available = mem.get("MemAvailable", 0)
    cpu = float(affinity)
    memory_limit = total
    headroom = available
    groups = cgroup_directories(root)
    stats = {"cpu": [], "memory": []}
    for directory, kind in groups["cpu"]:
        if kind == "cgroup2":
            values = read(directory / "cpu.max").split()
        else:
            values = [read(directory / "cpu.cfs_quota_us"), read(directory / "cpu.cfs_period_us")]
        try:
            quota, period = map(int, values)
            if quota > 0 and period > 0:
                cpu = min(cpu, quota / period)
        except (ValueError, TypeError):
            pass
        stats["cpu"].append(counters(directory / "cpu.stat"))
    for directory, kind in groups["memory"]:
        limit_file, current_file = ("memory.max", "memory.current") if kind == "cgroup2" else ("memory.limit_in_bytes", "memory.usage_in_bytes")
        try:
            limit = int(read(directory / limit_file))
            if 0 < limit <= total:
                memory_limit = min(memory_limit, limit)
                headroom = min(headroom, limit)
                current = int(read(directory / current_file))
                headroom = min(headroom, max(0, limit - current))
        except ValueError:
            pass
        stats["memory"].append(counters(directory / "memory.events"))
    cpu_line = read(root / "proc/stat").splitlines()
    cpu_ticks = cpu_line[0].split()[1:] if cpu_line and cpu_line[0].startswith("cpu ") else []
    vm = counters(root / "proc/vmstat")
    return {
        "affinityCpus": affinity,
        "effectiveCpuQuota": cpu,
        "hostMemoryBytes": total,
        "hostAvailableMemoryBytes": available,
        "effectiveMemoryLimitBytes": memory_limit,
        "availableMemoryBytes": headroom,
        "visibleCgroupLevels": {key: len(value) for key, value in groups.items()},
        "cgroupCounters": stats,
        "hostCpuTicks": dict(zip(("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal", "guest", "guestNice"), map(int, cpu_ticks))),
        "swapCounters": {key: vm.get(key) for key in ("pswpin", "pswpout")},
        "pressure": {name: read(root / ("proc/pressure/" + name)) for name in ("cpu", "memory", "io")},
        "note": "Only visible cgroup ancestors can be measured; hidden parent limits require host inspection.",
    }


def select_jobs(report, shares=1, maximum="auto"):
    if shares < 1:
        raise ValueError("resource shares must be positive")
    # MemAvailable already excludes memory in use by the OS/build daemon.
    # Reserve another 512 MiB and budget 1.75 GiB per compiler worker.
    # The measured 4-core runner had 6.4-6.7 GiB available at startup;
    # the former 1 + 2 GiB rule rounded that down to only two workers.
    # Each independent concurrent BuildKit stage receives one share.
    cpu_jobs = max(1, math.floor(report["effectiveCpuQuota"] / shares))
    memory_jobs = max(0, (report["availableMemoryBytes"] - BUILD_RESERVE_BYTES) // (WORKER_MEMORY_BYTES * shares))
    if memory_jobs < 1:
        raise ValueError("insufficient available RAM for bounded compilation: need 512 MiB reserve plus 1.75 GiB per active stage")
    jobs = min(cpu_jobs, memory_jobs)
    if maximum != "auto":
        if not str(maximum).isascii() or not str(maximum).isdigit() or int(maximum) < 1:
            raise ValueError("NODE_BUILD_JOBS must be auto or a positive integer")
        jobs = min(jobs, int(maximum))
    return int(jobs)


def apply_budget(report, cpu_limit, memory_limit):
    """Cap discovery with the executor budget hidden by nested BuildKit mounts."""
    cpu = float(cpu_limit)
    memory = int(memory_limit)
    if not math.isfinite(cpu) or cpu <= 0 or memory <= 0:
        raise ValueError("build CPU and memory budgets must be positive and finite")
    report["configuredCpuBudget"] = cpu
    report["configuredMemoryBudgetBytes"] = memory
    report["effectiveCpuQuota"] = min(report["effectiveCpuQuota"], cpu)
    report["effectiveMemoryLimitBytes"] = min(report["effectiveMemoryLimitBytes"], memory)
    report["availableMemoryBytes"] = min(report["availableMemoryBytes"], memory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shares", type=int, default=1)
    parser.add_argument("--max-jobs", default=os.environ.get("NODE_BUILD_JOBS", "auto"))
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--cpu-limit", default=os.environ.get("NODE_BUILD_CPU_LIMIT", "3"))
    parser.add_argument("--memory-limit-bytes", default=os.environ.get("NODE_BUILD_MEMORY_LIMIT_BYTES", str(8 * GIB)))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = collect()
    report["diskFreeBytes"] = shutil.disk_usage(".").free
    report["resourceShares"] = args.shares
    report["buildReserveBytes"] = BUILD_RESERVE_BYTES
    report["workerMemoryBytes"] = WORKER_MEMORY_BYTES
    try:
        apply_budget(report, args.cpu_limit, args.memory_limit_bytes)
        report["selectedJobs"] = select_jobs(report, args.shares, args.max_jobs)
    except ValueError as error:
        report["selectionError"] = str(error)
    payload = json.dumps(report, sort_keys=True)
    print("BUILD_RESOURCES " + payload, file=sys.stderr)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n")
    if args.report_only:
        return 0
    if "selectionError" in report:
        return 1
    print(report["selectedJobs"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
