"""Small standard-library HTTP service used only to attest Python runtime behavior."""

from __future__ import annotations

import hashlib
import json
import os
import ssl
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ASSURANCE_LEVEL = os.environ.get("IHL_ASSURANCE_LEVEL", "unknown")
FIPS_MODULE = "/opt/openssl/lib/ossl-modules/fips.so"


def crypto_observation() -> dict[str, object]:
    md5_blocked = False
    approved_sha256_passed = False
    module_sha256 = ""
    diagnostic_error = ""
    try:
        approved_sha256_passed = bool(
            hashlib.sha256(b"Indian Hill approved algorithm probe").hexdigest()
        )
        try:
            hashlib.new("md5", b"Indian Hill prohibited algorithm probe", usedforsecurity=True)
        except ValueError:
            # Test algorithm rejection even when the named MD5 helper is absent.
            # Unexpected API failures remain diagnostic errors, not FIPS proof.
            md5_blocked = True
        with open(FIPS_MODULE, "rb") as stream:
            module_sha256 = hashlib.sha256(stream.read()).hexdigest()
    except Exception as error:  # diagnostics must report, rather than crash
        # Never close an attestation request without a response. A failed FIPS
        # operation is evidence for the pipeline, not an unreported outage.
        diagnostic_error = f"{type(error).__name__}: {error}"
    return {
        "applicable": ASSURANCE_LEVEL == "validated",
        "assuranceLevel": ASSURANCE_LEVEL,
        "opensslVersion": ssl.OPENSSL_VERSION,
        "approvedSha256Passed": approved_sha256_passed,
        "prohibitedMd5Blocked": md5_blocked,
        "fipsExpected": ASSURANCE_LEVEL == "validated",
        "standard": os.environ.get("IHL_FIPS_STANDARD"),
        "moduleName": os.environ.get("IHL_FIPS_MODULE_NAME"),
        "moduleVersion": os.environ.get("IHL_FIPS_MODULE_VERSION"),
        "cmvpCertificate": os.environ.get("IHL_FIPS_CMVP_CERTIFICATE"),
        "baseLibraryVersion": os.environ.get("IHL_OPENSSL_BASE_VERSION"),
        "modulePath": FIPS_MODULE,
        "moduleSha256": module_sha256,
        "configPath": "/opt/openssl/ssl/openssl-fips.cnf",
        "diagnosticError": diagnostic_error,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "IHL-Python"
    sys_version = ""

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/healthz":
            self.respond_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "artifact": "IHL-APP-0002",
                    "assuranceLevel": ASSURANCE_LEVEL,
                },
            )
            return
        if self.path == "/diagnostics/crypto":
            self.respond_json(HTTPStatus.OK, crypto_observation())
            return
        if self.path == "/":
            self.respond_json(
                HTTPStatus.OK,
                {
                    "artifact": os.environ.get("IHL_ARTIFACT_ID", "IHL-CTR-0003"),
                    "assuranceLevel": ASSURANCE_LEVEL,
                    "effectiveUid": os.geteuid(),
                    "runtimeVersion": sys.version.split()[0],
                },
            )
            return
        self.respond_json(HTTPStatus.NOT_FOUND, {"status": "not-found"})

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        self.respond_json(HTTPStatus.METHOD_NOT_ALLOWED, {"status": "method-not-allowed"})

    def respond_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
