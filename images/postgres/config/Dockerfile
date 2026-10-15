# PostgreSQL is compiled from the checksum-pinned upstream source and linked to
# the controlled OpenSSL runtime. The delivered Ubuntu Chiseled image has no
# package manager, compiler, or embedded database credentials. PostgreSQL's
# upstream initdb invokes postgres through POSIX popen during first-run
# initialization, so the minimal /bin/sh runtime dependency is retained.
ARG POSTGRES_BUILDER=docker.io/library/gcc:11.2.0@sha256:2c5cae6b84598eb6865d6c7b340deef80e8834a4c4037a5cbba755a5258809d4
ARG POSTGRES_BASE=mcr.microsoft.com/dotnet/runtime-deps:10.0.13-noble-chiseled-amd64@sha256:e6cb0d241bab6f29daf92f2e11b3e605e0b0df4face98a71811c084aafa45593

FROM ${POSTGRES_BUILDER} AS openssl-supported-base-build
ARG OPENSSL_BASE_VERSION=3.5.9
ARG OPENSSL_BASE_SOURCE_SHA256=603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a
ADD --checksum=sha256:603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a https://www.openssl.org/source/openssl-3.5.9.tar.gz /tmp/openssl.tar.gz
RUN set -eu; \
    printf '%s  %s\n' "$OPENSSL_BASE_SOURCE_SHA256" /tmp/openssl.tar.gz | sha256sum --check --strict; \
    tar -xzf /tmp/openssl.tar.gz -C /tmp; \
    cd "/tmp/openssl-$OPENSSL_BASE_VERSION"; \
    ./Configure no-fips --prefix=/opt/openssl --openssldir=/opt/openssl/ssl --libdir=lib; \
    make -s -j2; make -s install_sw install_ssldirs; \
    install -d -m 0755 /opt/openssl/share/licenses/openssl; \
    install -m 0644 LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt

FROM ${POSTGRES_BUILDER} AS postgres-build
ARG POSTGRES_VERSION=16.15
ARG POSTGRES_SOURCE_SHA256=4f200ca23dfb120ff9838f13ce06014aad1d3c432d16ee9f93ab2000c0eeef7b
COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl
ADD --checksum=sha256:4f200ca23dfb120ff9838f13ce06014aad1d3c432d16ee9f93ab2000c0eeef7b https://ftp.postgresql.org/pub/source/v16.15/postgresql-16.15.tar.gz /tmp/postgresql.tar.gz
COPY images/postgres/config/ihl-postgres-entrypoint.c /tmp/ihl-postgres-entrypoint.c
RUN set -eu; \
    printf '%s  %s\n' "$POSTGRES_SOURCE_SHA256" /tmp/postgresql.tar.gz | sha256sum --check --strict; \
    tar -xzf /tmp/postgresql.tar.gz -C /tmp; \
    cd "/tmp/postgresql-$POSTGRES_VERSION"; \
    ./configure \
      --prefix=/opt/postgresql \
      --with-openssl \
      --without-readline \
      --without-zlib \
      --without-icu \
      --without-ldap \
      --without-pam \
      --without-gssapi \
      --without-systemd \
      --without-libxml \
      --without-libxslt \
      CFLAGS='-O2 -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=2 -I/opt/openssl/include' \
      LDFLAGS='-Wl,-z,relro,-z,now -Wl,-rpath,/opt/openssl/lib -L/opt/openssl/lib'; \
    make -s -j2; make -s install; \
    for tool in clusterdb createdb createuser dropdb dropuser pg_amcheck pg_basebackup pg_bench pg_config pg_ctl pg_dump pg_dumpall pg_isready pg_receivewal pg_recvlogical pg_resetwal pg_restore pg_rewind pg_test_fsync pg_test_timing pg_upgrade pg_verifybackup pg_waldump psql reindexdb vacuumdb; do rm -f "/opt/postgresql/bin/$tool"; done; \
    gcc -Os -fPIE -pie -Wl,-z,relro,-z,now -o /usr/local/bin/ihl-postgres-entrypoint /tmp/ihl-postgres-entrypoint.c; \
    ldd /opt/postgresql/bin/postgres > /tmp/postgres-linkage.txt; \
    ! grep -F 'not found' /tmp/postgres-linkage.txt; \
    grep -F '/opt/openssl/lib/libssl.so.3' /tmp/postgres-linkage.txt; \
    grep -F '/opt/openssl/lib/libcrypto.so.3' /tmp/postgres-linkage.txt

FROM ${POSTGRES_BASE}
ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
LABEL org.opencontainers.image.title="Indian Hill Secure PostgreSQL 16" \
      org.opencontainers.image.description="Minimal rootless PostgreSQL 16 server linked to a controlled OpenSSL 3.5.9 base library; includes only the POSIX shell runtime required by upstream initdb" \
      org.opencontainers.image.version="16.15-secure-candidate.1" \
      org.opencontainers.image.vendor="Indian Hill Labs" \
      org.opencontainers.image.licenses="PostgreSQL AND Apache-2.0" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="IHL-CTR-0004" \
      com.indianhilllabs.standard="IHL-SCS-001-v0.1-draft" \
      com.indianhilllabs.assurance.level="secure"
COPY --from=postgres-build /opt/postgresql /opt/postgresql
COPY --from=postgres-build /bin/dash /bin/sh
COPY --from=postgres-build /opt/openssl/lib/libcrypto.so.3 /opt/openssl/lib/libcrypto.so.3
COPY --from=postgres-build /opt/openssl/lib/libssl.so.3 /opt/openssl/lib/libssl.so.3
COPY --from=postgres-build /opt/openssl/share/licenses/openssl/LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt
COPY --from=postgres-build /usr/local/bin/ihl-postgres-entrypoint /usr/local/bin/ihl-postgres-entrypoint
# Explicit modes keep the immutable account database within the tailored CIS
# filesystem controls regardless of the source checkout's platform metadata.
COPY --chmod=0644 images/postgres/config/passwd /etc/passwd
COPY --chmod=0644 images/postgres/config/group /etc/group
COPY --chown=1654:1654 images/postgres/config/postgresql.secure.conf /opt/ihl/postgresql/postgresql.conf
COPY --chown=1654:1654 images/postgres/config/pg_hba.secure.conf /opt/ihl/postgresql/pg_hba.secure.conf
COPY --chown=1654:1654 images/postgres/config/pg_ident.conf /opt/ihl/postgresql/pg_ident.conf
# Keep the writable parent in the image without placing any content in PGDATA:
# upstream initdb rejects a non-empty data directory on first start.
COPY --chown=1654:1654 images/postgres/config/pg_ident.conf /var/lib/postgresql/.keep
ENV IHL_ASSURANCE_LEVEL="secure" \
    PGDATA="/var/lib/postgresql/data" \
    LD_LIBRARY_PATH="/opt/openssl/lib" \
    PATH="/opt/postgresql/bin"
USER 1654:1654
WORKDIR /var/lib/postgresql/data
EXPOSE 5432
ENTRYPOINT ["/usr/local/bin/ihl-postgres-entrypoint"]
STOPSIGNAL SIGINT

LABEL com.indianhilllabs.artifact.role="production"
