"use strict";

// Standard-library-only test consumer for the reusable Node.js runtime.
const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");

const ASSURANCE_LEVEL = process.env.IHL_ASSURANCE_LEVEL || "unknown";
const FIPS_MODULE = "/opt/openssl/lib/ossl-modules/fips.so";

function cryptoObservation() {
  let approvedSha256Passed = false;
  let prohibitedMd5Blocked = false;
  let moduleSha256 = "";
  let diagnosticError = "";

  try {
    approvedSha256Passed = Boolean(
      crypto.createHash("sha256").update("Indian Hill approved algorithm probe").digest("hex"),
    );
    try {
      crypto.createHash("md5").update("Indian Hill prohibited algorithm probe").digest("hex");
    } catch (_error) {
      prohibitedMd5Blocked = true;
    }
    moduleSha256 = crypto.createHash("sha256").update(fs.readFileSync(FIPS_MODULE)).digest("hex");
  } catch (error) {
    diagnosticError = `${error.name}: ${error.message}`;
  }

  return {
    applicable: ASSURANCE_LEVEL === "validated",
    assuranceLevel: ASSURANCE_LEVEL,
    nodeVersion: process.version,
    opensslVersion: process.versions.openssl,
    fipsModeEnabled: crypto.getFips() === 1,
    approvedSha256Passed,
    prohibitedMd5Blocked,
    fipsExpected: ASSURANCE_LEVEL === "validated",
    standard: process.env.IHL_FIPS_STANDARD,
    moduleName: process.env.IHL_FIPS_MODULE_NAME,
    moduleVersion: process.env.IHL_FIPS_MODULE_VERSION,
    cmvpCertificate: process.env.IHL_FIPS_CMVP_CERTIFICATE,
    baseLibraryVersion: process.env.IHL_OPENSSL_BASE_VERSION,
    modulePath: FIPS_MODULE,
    moduleSha256,
    configPath: "/opt/openssl/ssl/nodejs-fips.cnf",
    diagnosticError,
  };
}

function respond(response, status, body) {
  const payload = Buffer.from(JSON.stringify(body));
  response.writeHead(status, {
    "cache-control": "no-store",
    "content-length": String(payload.length),
    "content-type": "application/json",
  });
  response.end(payload);
}

http.createServer((request, response) => {
  if (request.method !== "GET") {
    respond(response, 405, { status: "method-not-allowed" });
    return;
  }
  if (request.url === "/healthz") {
    respond(response, 200, { status: "ok", artifact: "IHL-APP-0003", assuranceLevel: ASSURANCE_LEVEL });
    return;
  }
  if (request.url === "/diagnostics/crypto") {
    respond(response, 200, cryptoObservation());
    return;
  }
  if (request.url === "/") {
    respond(response, 200, {
      artifact: process.env.IHL_ARTIFACT_ID || "IHL-CTR-0005",
      assuranceLevel: ASSURANCE_LEVEL,
      effectiveUid: process.getuid(),
      runtimeVersion: process.versions.node,
    });
    return;
  }
  respond(response, 404, { status: "not-found" });
}).listen(8080, "0.0.0.0");
