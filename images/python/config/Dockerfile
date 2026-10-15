# CPython is compiled from the checksum-pinned upstream release and linked to
# an explicitly controlled OpenSSL 3.5.9 runtime. The final Ubuntu Chiseled
# image deliberately contains no package manager, compiler, shell, or pip.
ARG PYTHON_BUILDER=docker.io/library/ubuntu:24.04@sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254
ARG PYTHON_BASE=mcr.microsoft.com/dotnet/runtime-deps:10.0.13-noble-chiseled-amd64@sha256:e6cb0d241bab6f29daf92f2e11b3e605e0b0df4face98a71811c084aafa45593

# General-purpose compilation follows the supported Noble runtime, independently
# of the frozen FIPS module toolchain in Dockerfile.validated. Never bypass APT
# signature or Release-file freshness checks to keep an EOL builder working.
FROM ${PYTHON_BUILDER} AS python-toolchain

RUN set -eu; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get -o APT::Update::Error-Mode=any update; \
    apt-get install --yes --no-install-recommends \
      build-essential \
      ca-certificates \
      libbz2-dev \
      libexpat1-dev \
      libffi-dev \
      libgdbm-dev \
      liblzma-dev \
      libncurses-dev \
      libreadline-dev \
      libsqlite3-dev \
      perl \
      uuid-dev \
      xz-utils \
      zlib1g-dev; \
    rm -rf /var/lib/apt/lists/*

FROM python-toolchain AS openssl-supported-base-build

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
    printf '%s  %s\n' "$OPENSSL_BASE_SOURCE_SHA256" /tmp/openssl-3.5.9.tar.gz | sha256sum --check --strict; \
    tar --extract --gzip --file /tmp/openssl-3.5.9.tar.gz --directory /tmp; \
    cd "/tmp/openssl-$OPENSSL_BASE_VERSION"; \
    run_logged /tmp/openssl-base-configure.log ./Configure no-fips --prefix=/opt/openssl --openssldir=/opt/openssl/ssl --libdir=lib; \
    run_logged /tmp/openssl-base-build.log make -j2; \
    run_logged /tmp/openssl-base-install.log make install_sw install_ssldirs; \
    install -d -m 0755 /opt/openssl/share/licenses/openssl; \
    install -m 0644 LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt

FROM python-toolchain AS python-build

ARG PYTHON_BUILDER
ARG PYTHON_VERSION=3.13.16
ARG PYTHON_SOURCE_SHA256=f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d
ARG OPENSSL_BASE_SOURCE_SHA256=603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a

COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl

ADD --checksum=sha256:f4b1bfb3c79b5bb11b8d228a12504163b4c0dab4d679828d8f5f26b6cb6ab35d \
    https://www.python.org/ftp/python/3.13.16/Python-3.13.16.tar.xz \
    /tmp/Python-3.13.16.tar.xz

RUN set -eu; \
    run_logged() { \
      log="$1"; shift; \
      if ! "$@" >"$log" 2>&1; then \
        printf 'ERROR: CPython build command failed: %s\n' "$*" >&2; \
        tail -n 250 "$log" >&2; \
        exit 1; \
      fi; \
    }; \
    printf '%s  %s\n' "$PYTHON_SOURCE_SHA256" /tmp/Python-3.13.16.tar.xz | sha256sum --check --strict; \
    tar --extract --xz --file /tmp/Python-3.13.16.tar.xz --directory /tmp; \
    cd "/tmp/Python-$PYTHON_VERSION"; \
    run_logged /tmp/python-configure.log ./configure \
      --prefix=/opt/python \
      --with-ensurepip=no \
      --without-builtin-hashlib-hashes \
      --with-openssl=/opt/openssl \
      --with-openssl-rpath=auto \
      --without-static-libpython; \
    run_logged /tmp/python-build.log make -j2; \
    run_logged /tmp/python-install.log make altinstall; \
    ln -s python3.13 /opt/python/bin/python3; \
    ln -s python3.13 /opt/python/bin/python; \
    export LD_LIBRARY_PATH=/opt/openssl/lib; \
    /opt/python/bin/python3 -I -c 'import hashlib, ssl, sys; assert sys.version_info[:2] == (3, 13); assert ssl.OPENSSL_VERSION.startswith("OpenSSL 3.5.9 "); assert hashlib.sha256(b"Indian Hill Python Secure").hexdigest()'; \
    ldd /opt/python/lib/python3.13/lib-dynload/_ssl*.so > /tmp/python-ssl-linkage.txt; \
    ! grep -F 'not found' /tmp/python-ssl-linkage.txt; \
    grep -F '/opt/openssl/lib/libssl.so.3' /tmp/python-ssl-linkage.txt; \
    grep -F '/opt/openssl/lib/libcrypto.so.3' /tmp/python-ssl-linkage.txt; \
    install -d -m 0755 /opt/python/share/indianhilllabs; \
    { \
      printf 'pythonBuilder=%s\n' "$PYTHON_BUILDER"; \
      printf 'pythonSourceVersion=%s\n' "$PYTHON_VERSION"; \
      printf 'pythonSourceArchiveSha256=%s\n' "$PYTHON_SOURCE_SHA256"; \
      printf 'opensslBaseVersion=3.5.9\n'; \
      printf 'opensslBaseSourceArchiveSha256=%s\n' "$OPENSSL_BASE_SOURCE_SHA256"; \
      /opt/python/bin/python3 --version; \
      /opt/python/bin/python3 -I -c 'import ssl; print(ssl.OPENSSL_VERSION)'; \
      sha256sum /opt/python/lib/python3.13/lib-dynload/_ssl*.so; \
    } > /opt/python/share/indianhilllabs/build-info.txt

FROM ${PYTHON_BASE}

ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"

LABEL org.opencontainers.image.title="Indian Hill Secure Python 3.13 Runtime" \
      org.opencontainers.image.description="Minimal non-root CPython 3.13 runtime linked to a controlled OpenSSL 3.5.9 base library" \
      org.opencontainers.image.version="3.13.16-secure-lab.1" \
      org.opencontainers.image.vendor="Indian Hill Labs" \
      org.opencontainers.image.licenses="PSF-2.0 AND Apache-2.0" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="IHL-CTR-0003" \
      com.indianhilllabs.standard="IHL-SCS-001-v0.1-draft" \
      com.indianhilllabs.assurance.level="secure"

COPY --from=python-build /opt/python /opt/python
COPY --from=python-build /opt/openssl/lib/libcrypto.so.3 /opt/openssl/lib/libcrypto.so.3
COPY --from=python-build /opt/openssl/lib/libssl.so.3 /opt/openssl/lib/libssl.so.3
COPY --from=python-build /opt/openssl/share/licenses/openssl/LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt
# Noble is usr-merged. Include the versioned SONAME links AND their objects,
# not the unversioned development symlinks. Keep the final base's libc/loader.
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libbz2.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libexpat.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libffi.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libgdbm.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/liblzma.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libncursesw.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libreadline.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libsqlite3.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libtinfo.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libuuid.so.* /lib/x86_64-linux-gnu/
COPY --from=python-build /usr/lib/x86_64-linux-gnu/libz.so.* /lib/x86_64-linux-gnu/

ENV IHL_ASSURANCE_LEVEL="secure" \
    PYTHONHOME="/opt/python" \
    PYTHONNOUSERSITE="1" \
    PYTHONUNBUFFERED="1" \
    SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt" \
    SSL_CERT_DIR="/etc/ssl/certs" \
    LD_LIBRARY_PATH="/opt/openssl/lib"

USER 1654:1654
WORKDIR /app
# The custom OpenSSL prefix has no CA bundle of its own. Verify that the
# standard SSL context loads the inherited system trust store as the final UID.
RUN ["/opt/python/bin/python3", "-I", "-c", "import ssl; context = ssl.create_default_context(); assert context.get_ca_certs(), 'system trust roots missing'; assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname"]
ENTRYPOINT ["/opt/python/bin/python3"]
CMD ["--version"]

LABEL com.indianhilllabs.artifact.role="production"
