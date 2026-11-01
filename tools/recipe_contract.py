"""Validate reviewed recipe pins without accepting arbitrary build overrides.

Copyright 2026 Indian Hill Labs
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import re


PREFIXES = {name: name.upper() for name in (
    "aspnet", "nginx", "python", "node", "postgres", "redis", "tomcat", "elasticsearch")}


def image_build_args(product: dict, tier: str, recipe: dict | None = None) -> dict[str, str]:
    recipe = recipe if recipe is not None else product["image"]["tiers"][tier]
    args = recipe.get("buildArgs", {})
    if not isinstance(args, dict):
        raise ValueError("image buildArgs must be an object")
    family = product.get("family")
    if family == "go":
        controlled = {"go": ("1.27", "IHL-CTR-0010"), "go-1-26": ("1.26", "IHL-CTR-0035")}
        line, identity = controlled.get(product.get("key"), (None, None))
        version = product.get("productVersion")
        if (line is None or product.get("versionLine") != line or product.get("id") != identity
                or product.get("targetId") != "go-" + line or product.get("kind") != "runtime-base"
                or product.get("assessmentTiers") != ["secure", "hardened"]
                or product.get("image", {}).get("repository") != "go"
                or not isinstance(version, str) or not re.fullmatch(re.escape(line) + r"\.[0-9]+", version)
                or tier not in {"secure", "hardened"}
                or recipe.get("dockerfile") != "images/go/config/Dockerfile" + (".hardened" if tier == "hardened" else "")):
            raise ValueError("Go recipe pins require an exact controlled bare runtime product")
        expected = {"GO_PRODUCT_VERSION": version, "GO_ARTIFACT_ID": identity} if tier == "secure" else {}
        if args != expected:
            raise ValueError("Go image buildArgs must contain exactly the reviewed version and identity pins")
        return dict(args)
    if not args:
        if family in PREFIXES and tier == "secure" and (product.get("key") == "nginx-mainline"
                or product.get("assessmentTiers") in (["secure"], ["secure", "hardened"])):
            raise ValueError("Versioned Secure image buildArgs require exact version, source and identity pins")
        if family in PREFIXES and tier == "hardened" and product.get("assessmentTiers") == ["secure", "hardened"]:
            raise ValueError("Hardened image buildArgs require exact version and identity pins")
        return {}
    prefix = PREFIXES.get(family)
    if tier not in {"secure", "hardened"} or not prefix:
        raise ValueError("image buildArgs are restricted to reviewed Secure/Hardened family recipes")
    required = {prefix + suffix for suffix in ("_VERSION", "_VERSION_LINE", "_ARTIFACT_ID")}
    if tier == "secure":
        if family in {"aspnet", "elasticsearch"}:
            required.add(prefix + "_BASE")
        elif family == "tomcat":
            required.update({"TOMCAT_MAJOR", "TOMCAT_SOURCE_SHA512"})
        else:
            required.add(prefix + "_SOURCE_SHA256")
        if family == "redis":
            required.add("REDIS_LICENSES")
    elif family == "redis":
        required.add("REDIS_CONFIG_FILE")
    if set(args) != required or any(not isinstance(value, str) for value in args.values()):
        raise ValueError("image buildArgs must contain exactly the reviewed family pins")
    version, line, identity = (product.get(field) for field in ("productVersion", "versionLine", "id"))
    if (not isinstance(version, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", version)
            or not isinstance(line, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", line)
            or not (version == line or version.startswith(line + "."))
            or not isinstance(identity, str) or not re.fullmatch(r"IHL-CTR-[0-9]{4}", identity)
            or any(args[prefix + suffix] != expected for suffix, expected in (
                ("_VERSION", version), ("_VERSION_LINE", line), ("_ARTIFACT_ID", identity)))):
        raise ValueError("image buildArgs differ from the selected full version or product identity")
    for key, value in args.items():
        if key == "REDIS_CONFIG_FILE":
            expected = ("images/redis/config/redis.hardened-6.2.conf" if line == "6.2"
                        else "images/redis/config/redis.hardened.conf")
            if value != expected:
                raise ValueError("Hardened Redis configuration differs from the reviewed version line")
        elif key.endswith("_BASE"):
            origin = (r"mcr\.microsoft\.com/dotnet/aspnet:" + re.escape(version) + r"-noble-chiseled-amd64"
                      if family == "aspnet" else r"docker\.elastic\.co/elasticsearch/elasticsearch:" + re.escape(version) + r"-amd64")
            if not re.fullmatch(origin + r"@sha256:[0-9a-f]{64}", value):
                raise ValueError("image buildArgs require the exact vendor image tag and digest")
        elif key.endswith("_SOURCE_SHA256"):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise ValueError("image buildArgs require a complete source SHA-256")
        elif key.endswith("_SOURCE_SHA512"):
            if not re.fullmatch(r"[0-9a-f]{128}", value):
                raise ValueError("image buildArgs require a complete source SHA-512")
        elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", value) or ".." in value:
            raise ValueError("image buildArgs contain an unsafe value")
    if tier == "secure" and family == "tomcat" and args["TOMCAT_MAJOR"] != version.split(".")[0]:
        raise ValueError("image buildArgs Tomcat major differs from the full version")
    if tier == "secure" and family == "redis":
        expected_license = ("BSD-3-Clause" if line in {"6.2", "7.2"} else
                            "SSPL-1.0" if line == "7.4" else "AGPL-3.0-only")
        if args["REDIS_LICENSES"] != expected_license:
            raise ValueError("image buildArgs Redis license differs from the reviewed version line")
    return dict(args)
