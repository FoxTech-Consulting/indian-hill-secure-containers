#!/usr/bin/env python3
"""Execute the real Redis startup header against controlled OpenSSL failures.

Mandatory in Redis's existing gcc builder; no Docker daemon or OpenSSL SDK is
needed. The production source patch supplies main(), while only OpenSSL APIs
are substituted so initialization and qualification failures can be separated.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

CRYPTO = Path(__file__).resolve().parent
if not (CRYPTO / "ihl_crypto.h").is_file():
    CRYPTO = CRYPTO.parent / "images/redis/config/crypto"

STUB = r"""
#ifndef IHL_OPENSSL_TEST_STUB
#define IHL_OPENSSL_TEST_STUB
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { const char *name; } OSSL_PROVIDER;
typedef struct { int unused; } OPENSSL_INIT_SETTINGS;
typedef struct { int unused; } EVP_MD;
typedef struct { int unused; } EVP_RAND_CTX;
typedef struct { int unused; } EVP_RAND;
static OSSL_PROVIDER test_base = {"base"}, test_fips = {"fips"};
static OPENSSL_INIT_SETTINGS test_settings;
static EVP_MD test_md;
static EVP_RAND_CTX test_rng;
static EVP_RAND test_rand;
#define OPENSSL_INIT_LOAD_CONFIG 1
static int test_call(const char *name) {
    const char *failure = getenv("IHL_STUB_FAIL");
    puts(name);
    return !failure || strcmp(name, failure) != 0;
}
static OPENSSL_INIT_SETTINGS *OPENSSL_INIT_new(void) { return test_call("settings") ? &test_settings : NULL; }
static int OPENSSL_INIT_set_config_filename(OPENSSL_INIT_SETTINGS *s, const char *f) { return test_call("config-file"); }
static void OPENSSL_INIT_set_config_file_flags(OPENSSL_INIT_SETTINGS *s, unsigned long f) {}
static int OPENSSL_init_crypto(unsigned long f, OPENSSL_INIT_SETTINGS *s) { return test_call("initialize"); }
static void OPENSSL_INIT_free(OPENSSL_INIT_SETTINGS *s) {}
static int OSSL_PROVIDER_set_default_search_path(void *c, const char *p) { return test_call("module-path"); }
static OSSL_PROVIDER *OSSL_PROVIDER_load(void *c, const char *name) {
    return test_call(name) ? (strcmp(name, "base") == 0 ? &test_base : &test_fips) : NULL;
}
static int EVP_default_properties_enable_fips(void *c, int enabled) { return test_call("configure-fips"); }
static int OSSL_PROVIDER_self_test(OSSL_PROVIDER *p) { return test_call("self-test"); }
static int EVP_default_properties_is_fips_enabled(void *c) { return test_call("fips-enabled"); }
static EVP_MD *EVP_MD_fetch(void *c, const char *name, const char *props) {
    if (strcmp(name, "MD5") == 0) return test_call("md5-rejection") ? NULL : &test_md;
    return test_call("approved-sha256") ? &test_md : NULL;
}
static const OSSL_PROVIDER *EVP_MD_get0_provider(EVP_MD *md) { return test_call("digest-provider") ? &test_fips : &test_base; }
static const char *OSSL_PROVIDER_get0_name(const OSSL_PROVIDER *p) { return p->name; }
static void EVP_MD_free(EVP_MD *md) {}
static void ERR_clear_error(void) {}
static int RAND_bytes_ex(void *c, unsigned char *data, size_t len, unsigned int strength) { return test_call("random"); }
static EVP_RAND_CTX *RAND_get0_public(void *c) { return test_call("rng") ? &test_rng : NULL; }
static EVP_RAND *EVP_RAND_CTX_get0_rand(EVP_RAND_CTX *r) { return &test_rand; }
static const OSSL_PROVIDER *EVP_RAND_get0_provider(EVP_RAND *r) { return test_call("rng-provider") ? &test_fips : &test_base; }
static void OPENSSL_cleanse(void *p, size_t len) {}
static int EVP_Q_digest(void *c, const char *name, const char *props, const void *data,
                       size_t len, unsigned char *out, size_t *written) { *written = 32; return 1; }
#endif
"""


def compiler():
    for name in ("cc", "gcc", "clang"):
        if found := shutil.which(name):
            return found, dict(os.environ), False
    # Visual Studio is not necessarily in PATH for a Windows desktop session.
    installer = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    if os.name == "nt" and installer.is_file():
        result = subprocess.run([str(installer), "-latest", "-products", "*", "-find",
            r"VC\Tools\MSVC\**\bin\Hostx64\x64\cl.exe"], capture_output=True, text=True, check=True, timeout=15)
        paths = result.stdout.splitlines()
        if paths:
            executable = Path(paths[0])
            msvc = executable.parents[3]
            sdk = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Windows Kits/10"
            versions = sorted(p for p in (sdk / "Include").glob("*") if (p / "ucrt").is_dir())
            if versions:
                include = versions[-1]
                environment = dict(os.environ)
                environment["PATH"] = str(executable.parent) + os.pathsep + environment.get("PATH", "")
                environment["INCLUDE"] = os.pathsep.join(map(str, [msvc / "include", include / "ucrt", include / "shared", include / "um"]))
                environment["LIB"] = os.pathsep.join(map(str, [msvc / "lib/x64", sdk / "Lib" / include.name / "ucrt/x64", sdk / "Lib" / include.name / "um/x64"]))
                return str(executable), environment, True
    raise RuntimeError("Redis startup regression tests require a C compiler (provided by the Redis gcc builder)")


class RedisStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="redis-startup-")
        cls.directory = Path(cls.temporary.name)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.cc, cls.environment, cls.msvc = compiler()
        cls.root = cls.directory / "source"
        src = cls.root / "src"
        src.mkdir(parents=True)
        (src / "server.h").write_text("")
        (src / "server.c").write_bytes(b'#include "server.h"\nint main(int argc, char **argv) {\n    puts("redis-ready");\n    return 0;\n}\n')
        (src / "acl.c").write_bytes(b'#include "sha256.h"\n    SHA256_CTX ctx;\n    unsigned char hash[SHA256_BLOCK_SIZE];\n    sha256_init(&ctx);\n    sha256_update(&ctx,(unsigned char*)cleartext,len);\n    sha256_final(&ctx,hash);\n')
        (src / "util.c").write_bytes(b'/* Get random bytes, attempts to get an initial seed */\nold-body\n/* Generate the Redis "Run ID" */\n')
        spec = importlib.util.spec_from_file_location("redis_startup_source_patch", CRYPTO / "patch_source.py")
        patcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(patcher)
        patcher.patch(cls.root)
        openssl = cls.directory / "openssl"
        openssl.mkdir()
        for name in ("crypto.h", "evp.h", "err.h", "provider.h", "rand.h"):
            (openssl / name).write_text(STUB)
        cls.executables = {}
        for label, value in (("hardened", 0), ("validated", 1), ("default", None)):
            result, executable = cls.compile(label, value)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            cls.executables[label] = executable

    @classmethod
    def compile(cls, label, value):
        executable = cls.directory / (label + (".exe" if os.name == "nt" else ""))
        source = cls.root / "src/server.c"
        definition = [] if value is None else [f"-DIHL_REDIS_FIPS_VALIDATION={value}"]
        if cls.msvc:
            args = [cls.cc, "/nologo", "/std:c11", "/W0", f"/I{cls.directory}", *definition,
                    str(source), f"/Fe:{executable}", f"/Fo:{cls.directory / (label + '.obj')}"]
        else:
            args = [cls.cc, "-std=c11", "-I", str(cls.directory), *definition, str(source), "-o", str(executable)]
        result = subprocess.run(args, env=cls.environment, cwd=cls.directory, capture_output=True, text=True, timeout=30)
        return result, executable

    def invoke(self, label, *arguments, **environment):
        env = dict(self.environment)
        for key in ("OPENSSL_CONF", "OPENSSL_MODULES", "IHL_STUB_FAIL", "IHL_FIPS_BUILD_VALIDATION", "IHL_REDIS_FIPS_VALIDATION"):
            env.pop(key, None)
        env.update(environment)
        return subprocess.run([str(self.executables[label]), *arguments], env=env,
                              capture_output=True, text=True, timeout=10)

    def test_hardened_version_keeps_initialization_without_explicit_fips_validation(self):
        for failure in ("self-test", "fips-enabled", "approved-sha256", "digest-provider", "md5-rejection", "rng-provider"):
            with self.subTest(failure=failure):
                result = self.invoke("hardened", "--version", IHL_STUB_FAIL=failure)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("configure-fips", result.stdout)
                self.assertIn("redis-ready", result.stdout)
                self.assertNotIn("self-test", result.stdout)
                self.assertNotIn("md5-rejection", result.stdout)

    def test_hardened_still_fails_provider_initialization_and_overrides(self):
        for failure in ("settings", "initialize", "base", "fips", "configure-fips"):
            with self.subTest(failure=failure):
                self.assertEqual(self.invoke("hardened", "--version", IHL_STUB_FAIL=failure).returncode, 78)
        for env in ({"OPENSSL_CONF": "/dev/null"}, {"OPENSSL_MODULES": "/tmp"}):
            with self.subTest(env=env):
                self.assertEqual(self.invoke("hardened", "--version", **env).returncode, 78)

    def test_direct_validated_default_keeps_explicit_fips_validation(self):
        for label in ("validated", "default"):
            for failure in ("self-test", "fips-enabled", "approved-sha256", "digest-provider", "md5-rejection", "rng-provider"):
                with self.subTest(label=label, failure=failure):
                    self.assertEqual(self.invoke(label, "--version", IHL_STUB_FAIL=failure).returncode, 78)
            self.assertEqual(self.invoke(label, "--version").returncode, 0)

    def test_explicit_probe_validates_exact_hardened_binary(self):
        passed = self.invoke("hardened", "--ihl-crypto-check")
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertIn("IHL Redis cryptographic checks passed", passed.stdout)
        self.assertNotIn("redis-ready", passed.stdout)
        for failure in ("self-test", "fips-enabled", "approved-sha256", "digest-provider", "md5-rejection", "rng-provider"):
            with self.subTest(failure=failure):
                self.assertEqual(self.invoke("hardened", "--ihl-crypto-check", IHL_STUB_FAIL=failure).returncode, 78)

    def test_environment_cannot_change_baked_validation_default_or_disable_explicit_probe(self):
        overrides = {"IHL_FIPS_BUILD_VALIDATION": "false", "IHL_REDIS_FIPS_VALIDATION": "0", "IHL_STUB_FAIL": "self-test"}
        self.assertEqual(self.invoke("validated", "--version", **overrides).returncode, 78)
        self.assertEqual(self.invoke("hardened", "--ihl-crypto-check", **overrides).returncode, 78)
        overrides.update(IHL_FIPS_BUILD_VALIDATION="true", IHL_REDIS_FIPS_VALIDATION="1")
        self.assertEqual(self.invoke("hardened", "--version", **overrides).returncode, 0)

    def test_invalid_numeric_build_default_is_compile_error(self):
        result, _ = self.compile("invalid", 2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("IHL_REDIS_FIPS_VALIDATION must be 0 or 1", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
