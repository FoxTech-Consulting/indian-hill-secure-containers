# Node is built from the checksum-pinned upstream source against a controlled
# OpenSSL 3.5.9 shared library. The final Ubuntu Chiseled image deliberately
# contains neither a shell nor a package manager, npm, or Corepack.
ARG NODE_BUILDER=docker.io/library/gcc:12.2.0@sha256:a3e091325c0af43bc9c1c576ddd155351d5b16438124421188bb4b4fcacc1452
ARG NODE_BASE=mcr.microsoft.com/dotnet/runtime-deps:10.0.13-noble-chiseled-amd64@sha256:e6cb0d241bab6f29daf92f2e11b3e605e0b0df4face98a71811c084aafa45593

FROM ${NODE_BUILDER} AS openssl-supported-base-build

ARG NODE_BUILD_JOBS=auto
ARG NODE_BUILD_CPU_LIMIT=3
ARG NODE_BUILD_MEMORY_LIMIT_BYTES=8589934592
COPY images/node/config/build_resources.py /usr/local/lib/ihl-build-resources.py

ARG OPENSSL_BASE_VERSION=3.5.9
ARG OPENSSL_BASE_SOURCE_SHA256=603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a

ADD --checksum=sha256:603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a \
    https://www.openssl.org/source/openssl-3.5.9.tar.gz \
    /tmp/openssl-3.5.9.tar.gz

RUN set -eu; \
    run_logged() { \
      log="$1"; shift; \
      if ! "$@" >"$log" 2>&1; then \
        printf 'ERROR: OpenSSL build command failed: %s\n' "$*" >&2; \
        tail -n 250 "$log" >&2; \
        exit 1; \
      fi; \
    }; \
    run_progress_logged() { \
      log="$1"; shift; \
      status_file="${log}.status"; \
      rm -f "$status_file"; \
      (set +e; "$@" >"$log" 2>&1; status=$?; printf '%s\n' "$status" >"$status_file"; exit "$status") & \
      command_pid="$!"; \
      elapsed=0; \
      while kill -0 "$command_pid" 2>/dev/null; do \
        sleep 30; \
        if kill -0 "$command_pid" 2>/dev/null; then \
          elapsed=$((elapsed + 30)); \
          printf 'INFO: build command still running after %ss: %s\n' "$elapsed" "$*"; \
          if [ $((elapsed % 60)) -eq 0 ]; then python3 /usr/local/lib/ihl-build-resources.py --report-only; fi; \
          tail -n 1 "$log" || true; \
        fi; \
      done; \
      wait "$command_pid" || true; \
      status="$(cat "$status_file" 2>/dev/null || printf '125')"; \
      rm -f "$status_file"; \
      if [ "$status" -ne 0 ]; then \
        printf 'ERROR: OpenSSL build command failed: %s\n' "$*" >&2; \
        tail -n 250 "$log" >&2; \
        exit "$status"; \
      fi; \
    }; \
    printf '%s  %s\n' "$OPENSSL_BASE_SOURCE_SHA256" /tmp/openssl-3.5.9.tar.gz | sha256sum --check --strict; \
    tar --extract --gzip --file /tmp/openssl-3.5.9.tar.gz --directory /tmp; \
    cd "/tmp/openssl-$OPENSSL_BASE_VERSION"; \
    run_logged /tmp/openssl-base-configure.log ./Configure no-fips --prefix=/opt/openssl --openssldir=/opt/openssl/ssl --libdir=lib; \
    build_jobs="$(python3 /usr/local/lib/ihl-build-resources.py)"; \
    run_progress_logged /tmp/openssl-base-build.log make -j"$build_jobs"; \
    run_logged /tmp/openssl-base-install.log make install_sw install_ssldirs; \
    install -d -m 0755 /opt/openssl/share/licenses/openssl; \
    install -m 0644 LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt

FROM ${NODE_BUILDER} AS node-build

ARG NODE_BUILD_JOBS=auto
ARG NODE_BUILD_CPU_LIMIT=3
ARG NODE_BUILD_MEMORY_LIMIT_BYTES=8589934592
COPY images/node/config/build_resources.py /usr/local/lib/ihl-build-resources.py

ARG NODE_VERSION=24.20.0
ARG NODE_SOURCE_SHA256=987113866ab9018998f09f74072afe7136f3da8b934e35d89531e1e49890062f
ARG OPENSSL_BASE_SOURCE_SHA256=603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a

COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl

ADD --checksum=sha256:987113866ab9018998f09f74072afe7136f3da8b934e35d89531e1e49890062f \
    https://nodejs.org/dist/v24.20.0/node-v24.20.0.tar.gz \
    /tmp/node-v24.20.0.tar.gz

RUN set -eu; \
    command -v python3; \
    command -v pkg-config; \
    run_logged() { \
      log="$1"; shift; \
      if ! "$@" >"$log" 2>&1; then \
        printf 'ERROR: Node.js build command failed: %s\n' "$*" >&2; \
        tail -n 250 "$log" >&2; \
        exit 1; \
      fi; \
    }; \
    run_progress_logged() { \
      log="$1"; shift; \
      status_file="${log}.status"; \
      rm -f "$status_file"; \
      (set +e; "$@" >"$log" 2>&1; status=$?; printf '%s\n' "$status" >"$status_file"; exit "$status") & \
      command_pid="$!"; \
      elapsed=0; \
      while kill -0 "$command_pid" 2>/dev/null; do \
        sleep 30; \
        if kill -0 "$command_pid" 2>/dev/null; then \
          elapsed=$((elapsed + 30)); \
          printf 'INFO: build command still running after %ss: %s\n' "$elapsed" "$*"; \
          if [ $((elapsed % 60)) -eq 0 ]; then python3 /usr/local/lib/ihl-build-resources.py --report-only; fi; \
          tail -n 1 "$log" || true; \
        fi; \
      done; \
      wait "$command_pid" || true; \
      status="$(cat "$status_file" 2>/dev/null || printf '125')"; \
      rm -f "$status_file"; \
      if [ "$status" -ne 0 ]; then \
        printf 'ERROR: Node.js build command failed: %s\n' "$*" >&2; \
        tail -n 250 "$log" >&2; \
        exit "$status"; \
      fi; \
    }; \
    printf '%s  %s\n' "$NODE_SOURCE_SHA256" /tmp/node-v24.20.0.tar.gz | sha256sum --check --strict; \
    tar --extract --gzip --file /tmp/node-v24.20.0.tar.gz --directory /tmp; \
    cd "/tmp/node-v$NODE_VERSION"; \
    export LD_LIBRARY_PATH=/opt/openssl/lib; \
    export LDFLAGS='-Wl,-rpath,/opt/openssl/lib'; \
    run_logged /tmp/node-configure.log ./configure \
      --shared-openssl \
      --shared-openssl-includes=/opt/openssl/include \
      --shared-openssl-libpath=/opt/openssl/lib \
      --openssl-conf-name=nodejs_conf; \
    build_jobs="$(python3 /usr/local/lib/ihl-build-resources.py)"; \
    run_progress_logged /tmp/node-build.log make -j"$build_jobs"; \
    install -d -m 0755 /opt/node/bin /opt/node/share/indianhilllabs; \
    install -m 0755 out/Release/node /opt/node/bin/node; \
    ldd /opt/node/bin/node > /tmp/node-linkage.txt; \
    ! grep -F 'not found' /tmp/node-linkage.txt; \
    grep -F '/opt/openssl/lib/libssl.so.3' /tmp/node-linkage.txt; \
    grep -F '/opt/openssl/lib/libcrypto.so.3' /tmp/node-linkage.txt; \
    /opt/node/bin/node -e 'const assert = require("node:assert"); const crypto = require("node:crypto"); assert.strictEqual(process.version, "v24.20.0"); assert.strictEqual(process.versions.openssl, "3.5.9"); assert(crypto.createHash("sha256").update("Indian Hill Node Secure").digest("hex"));'; \
    { \
      printf 'nodeSourceVersion=%s\n' "$NODE_VERSION"; \
      printf 'nodeSourceArchiveSha256=%s\n' "$NODE_SOURCE_SHA256"; \
      printf 'opensslBaseVersion=3.5.9\n'; \
      printf 'opensslBaseSourceArchiveSha256=%s\n' "$OPENSSL_BASE_SOURCE_SHA256"; \
      /opt/node/bin/node --version; \
      /opt/node/bin/node -p 'process.versions.openssl'; \
      sha256sum /opt/node/bin/node; \
      cat /tmp/node-linkage.txt; \
    } > /opt/node/share/indianhilllabs/build-info.txt

FROM ${NODE_BASE}

ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"

LABEL org.opencontainers.image.title="Indian Hill Secure Node.js 24 Runtime" \
      org.opencontainers.image.description="Minimal non-root Node.js 24 runtime linked to a controlled OpenSSL 3.5.9 base library" \
      org.opencontainers.image.version="24.20.0-secure-lab.1" \
      org.opencontainers.image.vendor="Indian Hill Labs" \
      org.opencontainers.image.licenses="MIT AND Apache-2.0" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="IHL-CTR-0005" \
      com.indianhilllabs.standard="IHL-SCS-001-v0.1-draft" \
      com.indianhilllabs.assurance.level="secure"

COPY --from=node-build /opt/node /opt/node
COPY --from=node-build /opt/openssl/lib/libcrypto.so.3 /opt/openssl/lib/libcrypto.so.3
COPY --from=node-build /opt/openssl/lib/libssl.so.3 /opt/openssl/lib/libssl.so.3
COPY --from=node-build /opt/openssl/share/licenses/openssl/LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt
# Retain the Ubuntu base's packaged libstdc++ and libgcc. The GCC builder
# keeps its GCC 12 libraries in /usr/local/lib64; its /usr/lib copy is the
# older Debian runtime and must not overwrite Ubuntu's newer libraries.

ENV IHL_ASSURANCE_LEVEL="secure" \
    NODE_DISABLE_COLORS="1" \
    LD_LIBRARY_PATH="/opt/openssl/lib"

USER 1654:1654
WORKDIR /app
ENTRYPOINT ["/opt/node/bin/node"]
CMD ["--version"]

LABEL com.indianhilllabs.artifact.role="production"
