#!/usr/bin/env python3
"""Build unqualified local previews from a curated public source snapshot.

Copyright 2026 Indian Hill Labs
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path, PurePosixPath
from typing import Any


SOURCE_REPOSITORY = "https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
PLATFORM = "linux/amd64"
TIERS = ("secure", "hardened")
SHA256 = re.compile(r"[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}")
NAME = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")


def snapshot_path(root: Path, name: str) -> Path:
    """Reject paths that escape the public tree or depend on symlinks."""
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("Snapshot paths must be nonempty relative POSIX paths")
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError(f"Invalid snapshot path: {name}")
    target = root.joinpath(*relative.parts)
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Snapshot path escapes the repository: {name}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Snapshot paths cannot be symbolic links: {name}")
    if not target.is_file():
        raise ValueError(f"Snapshot file is missing: {name}")
    return target


def verify_snapshot(root: Path) -> dict[str, Any]:
    """Check the exported files, without treating checksums as authentication."""
    source = json.loads(snapshot_path(root, "SOURCE.json").read_text(encoding="utf-8"))
    if not isinstance(source, dict) or not REVISION.fullmatch(str(source.get("sourceRevision", ""))):
        raise ValueError("SOURCE.json must identify a full lowercase GitLab sourceRevision")
    entries = source.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("SOURCE.json must contain a nonempty exported files list")
    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("SOURCE.json has an invalid file entry")
        name = entry.get("path")
        target = snapshot_path(root, name)
        if name in names or name == "SOURCE.json":
            raise ValueError(f"SOURCE.json has a duplicate or self-referencing entry: {name}")
        names.add(name)
        expected = entry.get("sha256")
        if not isinstance(expected, str) or not SHA256.fullmatch(expected):
            raise ValueError(f"Invalid SHA-256 for exported file: {name}")
        contents = target.read_bytes()
        if hashlib.sha256(contents).hexdigest() != expected:
            raise ValueError(f"Snapshot checksum mismatch: {name}; use a reviewed snapshot or build modified sources directly")
        if "size" in entry and (type(entry["size"]) is not int or entry["size"] != len(contents)):
            raise ValueError(f"Snapshot size mismatch: {name}")
    if "public-products.json" not in names:
        raise ValueError("SOURCE.json does not cover public-products.json")
    return source


def recipe_path(root: Path, value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("images/"):
        raise ValueError("Public build recipes must be under images/")
    if "validated" in value.lower():
        raise ValueError("Validated build recipes are outside this public source snapshot")
    snapshot_path(root, value)
    return value


def product_tiers(product: dict[str, Any]) -> tuple[str, ...]:
    declared = product.get("assessmentTiers", list(TIERS))
    tiers = product.get("image", {}).get("tiers", {})
    if (declared not in (["secure"], list(TIERS)) or not isinstance(tiers, dict)
            or set(tiers) != set(declared)):
        raise ValueError(f"Public product recipes differ from supported assessment tiers: {product.get('key')}")
    return tuple(declared)


def public_build_args(product: dict[str, Any], tier: str, recipe: dict) -> dict[str, str]:
    # The exported helper is the same reviewed contract used by the factory.
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("ihl_recipe_contract", Path(__file__).with_name("recipe_contract.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.image_build_args(product, tier, recipe)


def read_catalog(root: Path, source: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = json.loads(snapshot_path(root, "public-products.json").read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or catalog.get("schemaVersion") != 1:
        raise ValueError("Unsupported public-products.json schema")
    if catalog.get("platform") != PLATFORM or catalog.get("tiers") != list(TIERS):
        raise ValueError("Public builds support only linux/amd64 Secure/Hardened recipes")
    products = catalog.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("Public catalog has no products")
    covered = {entry["path"] for entry in source["files"]}
    keys: set[str] = set()
    for product in products:
        if not isinstance(product, dict):
            raise ValueError("Invalid public product")
        key = product.get("key")
        if not isinstance(key, str) or not NAME.fullmatch(key) or key in keys:
            raise ValueError("Public product keys must be unique lowercase image names")
        keys.add(key)
        if not isinstance(product.get("productVersion"), str) or not VERSION.fullmatch(product["productVersion"]):
            raise ValueError(f"Invalid public product version: {key}")
        tiers = product.get("image", {}).get("tiers", {})
        supported = product_tiers(product)
        recipes = []
        for tier in supported:
            recipe = tiers[tier]
            if not isinstance(recipe, dict):
                raise ValueError(f"Invalid public recipe: {key}")
            recipes.append(recipe_path(root, recipe.get("dockerfile")))
            public_build_args(product, tier, recipe)
        workloads = product.get("workloads", [])
        if not isinstance(workloads, list):
            raise ValueError(f"Invalid public workloads: {key}")
        for workload in workloads:
            if not isinstance(workload, dict):
                raise ValueError(f"Invalid public workload: {key}")
            repository = workload.get("repository")
            if not isinstance(repository, str) or not NAME.fullmatch(repository):
                raise ValueError(f"Invalid public workload repository: {key}")
            recipes.append(recipe_path(root, workload.get("dockerfile")))
        if not set(recipes).issubset(covered):
            raise ValueError(f"SOURCE.json does not cover every build recipe for {key}")
    return products


def check_tag_prefix(prefix: str) -> None:
    # Only a local name prefix is needed; there is intentionally no push option.
    if not prefix or len(prefix) > 150 or not all(NAME.fullmatch(part) for part in prefix.split("/")):
        raise ValueError("--tag-prefix must contain lowercase name components separated by /")


def build_plan(product: dict[str, Any], revision: str, tier: str, *,
               with_example: bool = False, tag_prefix: str = "local/ihl",
               nonce: str | None = None) -> list[dict[str, Any]]:
    if tier not in TIERS or not REVISION.fullmatch(revision):
        raise ValueError("Local builds require a Secure/Hardened tier and full source revision")
    if tier not in product_tiers(product):
        raise ValueError(f"Unsupported assessment tier for {product['key']}: {tier}")
    check_tag_prefix(tag_prefix)
    workloads = product.get("workloads", [])
    if with_example and not workloads:
        raise ValueError(f"No public reference example is included for {product['key']}; build the runtime without --with-example")
    nonce = nonce or uuid.uuid4().hex[:12]
    if not re.fullmatch(r"[0-9a-f]{12}", nonce):
        raise ValueError("Invalid local parent identifier")
    key, version = product["key"], product["productVersion"]
    repository = f"{tag_prefix}/{key}"
    secure = f"{repository}:{version}-secure-local"
    # A unique alias avoids reusing another invocation's mutable Secure tag.
    parent = f"{repository}:{version}-secure-local-parent-{nonce}"

    def command(dockerfile: str, image: str, level: str, args: dict[str, str],
                aliases: tuple[str, ...] = ()) -> dict[str, Any]:
        argv = ["docker", "build", "--platform", PLATFORM, "--pull=false", "--file", dockerfile,
                "--tag", image]
        for alias in aliases:
            argv.extend(["--tag", alias])
        for name, value in {"OCI_SOURCE": SOURCE_REPOSITORY, "OCI_REVISION": revision, **args}.items():
            argv.extend(["--build-arg", f"{name}={value}"])
        for name, value in {
            "com.indianhilllabs.release.status": "local-unqualified",
            "com.indianhilllabs.assurance.qualification": "not-assessed",
            "com.indianhilllabs.assurance.level": level,
            "org.opencontainers.image.source": SOURCE_REPOSITORY,
            "org.opencontainers.image.revision": revision,
        }.items():
            argv.extend(["--label", f"{name}={value}"])
        argv.append(".")
        return {"image": image, "argv": argv}

    recipes = product["image"]["tiers"]
    steps = [command(recipes["secure"]["dockerfile"], secure, "secure",
                     public_build_args(product, "secure", recipes["secure"]),
                     (parent,) if tier == "hardened" else ())]
    runtime = secure
    if tier == "hardened":
        runtime = f"{repository}:{version}-hardened-local"
        args = public_build_args(product, "hardened", recipes["hardened"])
        steps.append(command(recipes["hardened"]["dockerfile"], runtime, "hardened", {**args, "SECURE_BASE": parent}))
    if with_example:
        for workload in workloads:
            image = f"{tag_prefix}/{key}-{workload['repository']}:{version}-{tier}-local"
            steps.append(command(workload["dockerfile"], image, tier,
                                 {"RUNTIME_BASE": runtime, "ASSURANCE_LEVEL": tier}))
    return steps


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("product", nargs="?", help="Product key from public-products.json")
    parser.add_argument("--tier", choices=TIERS, default="secure")
    parser.add_argument("--with-example", action="store_true", help="Also build the registered public reference workload")
    parser.add_argument("--tag-prefix", default="local/ihl", help="Local image name prefix (default: local/ihl)")
    parser.add_argument("--dry-run", action="store_true", help="Print command argument arrays without running Docker")
    parser.add_argument("--list", action="store_true", help="List public product versions and example availability")
    args = parser.parse_args(argv)
    if not args.product and not args.list:
        parser.error("choose a product or use --list")
    if args.product and args.list:
        parser.error("use --list without a product")
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    try:
        source = verify_snapshot(root)
        products = read_catalog(root, source)
        if args.list:
            for product in products:
                example = "example" if product.get("workloads") else "runtime only"
                print(f"{product['key']:16} {product['productVersion']:12} {PLATFORM:12} {example}")
            return 0
        product = next((item for item in products if item["key"] == args.product), None)
        if product is None:
            raise ValueError(f"Unknown product: {args.product}; use --list")
        steps = build_plan(product, source["sourceRevision"], args.tier,
                           with_example=args.with_example, tag_prefix=args.tag_prefix)
        if args.dry_run:
            for step in steps:
                print(json.dumps(step["argv"]))
            return 0
        for step in steps:
            print(f"Building local, unqualified image {step['image']}", flush=True)
            subprocess.run(step["argv"], cwd=root, check=True)
        print("Local builds completed. These images have not been qualified, signed, or published.")
        if args.tier == "hardened":
            print("The uniquely tagged Secure parent is retained locally for inspection; remove it when no longer needed.")
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(f"Build refused: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Docker build failed with exit code {exc.returncode}; no qualification was performed.", file=sys.stderr)
        return exc.returncode if 1 <= exc.returncode <= 125 else 1


if __name__ == "__main__":
    raise SystemExit(main())
