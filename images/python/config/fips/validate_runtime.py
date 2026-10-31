"""Fail-closed build smoke test in the exact Hardened Python userspace.

This script lives only in a disposable build stage. It supplements, not replaces,
the factory's digest-bound runtime, FIPS, vulnerability and compliance evidence.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import ssl
import sys
import _ssl


BOUNDARY_PATHS = {
    "/opt/openssl/lib/libssl.so.3",
    "/opt/openssl/lib/libcrypto.so.3",
    "/opt/openssl/lib/ossl-modules/fips.so",
}
BUILD_INFO = Path("/opt/openssl/share/indianhilllabs/fips-build-info.txt")


def verify_mappings(maps: str) -> list[str]:
    paths = {fields[5] for line in maps.splitlines()
             if len(fields := line.split(maxsplit=5)) == 6}
    names = {Path(path).name for path in BOUNDARY_PATHS}
    boundary = {path for path in paths
                if Path(path.removesuffix(" (deleted)")).name in names}
    if boundary != BOUNDARY_PATHS:
        raise ValueError(f"Python mapped an unexpected OpenSSL/FIPS boundary: {sorted(boundary)}")
    if _ssl.__file__ not in paths or not _ssl.__file__.startswith(
        f"/opt/python/lib/python{sys.version_info.major}.{sys.version_info.minor}/lib-dynload/_ssl."
    ):
        raise ValueError("Python did not map the inherited _ssl extension")
    return sorted(boundary | {_ssl.__file__})


def verify_runtime() -> list[str]:
    context = ssl.create_default_context()
    if not context.get_ca_certs() or context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
        raise ValueError("Python default TLS context lacks verified system trust roots")
    if not ssl.OPENSSL_VERSION.startswith("OpenSSL 3.5.9 "):
        raise ValueError("Python is not using the supported OpenSSL base library")
    if hashlib.sha256(b"abc").hexdigest() != (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    ):
        raise ValueError("Python SHA-256 known-answer test failed")
    try:
        # Strict builds can omit hashlib.md5 entirely. Exercise the real generic
        # constructor so a missing helper alone cannot be mistaken for rejection.
        hashlib.new("md5", b"prohibited", usedforsecurity=True)
    except ValueError:
        pass
    else:
        raise ValueError("Python resolved MD5 while fips=yes was enforced")
    return verify_mappings(Path("/proc/self/maps").read_text(encoding="utf-8"))


def main() -> None:
    validation = os.environ.get("IHL_FIPS_BUILD_VALIDATION", "true")
    if validation not in {"true", "false"}:
        raise ValueError("IHL_FIPS_BUILD_VALIDATION must be true or false")
    if validation == "false":
        print("INFO: selected Hardened skips Python build FIPS qualification probes")
        return
    mapped_paths = verify_runtime()
    lines = [ssl.OPENSSL_VERSION, "pythonRuntimeValidation=hardened-userspace"]
    for name in mapped_paths:
        lines.append(f"{hashlib.sha256(Path(name).read_bytes()).hexdigest()}  {name}")
    # Do not create evidence if the module's preceding build evidence is absent.
    with BUILD_INFO.open("r+", encoding="utf-8") as report:
        if not report.read().strip():
            raise ValueError("FIPS module build evidence is empty")
        report.write("\n".join(lines) + "\n")
    print("PASS: inherited Python _ssl uses the controlled FIPS boundary; MD5 rejected")


if __name__ == "__main__":
    main()
