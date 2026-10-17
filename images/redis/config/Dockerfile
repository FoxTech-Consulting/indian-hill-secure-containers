ARG REDIS_BUILDER=docker.io/library/gcc:11.2.0@sha256:2c5cae6b84598eb6865d6c7b340deef80e8834a4c4037a5cbba755a5258809d4
ARG REDIS_BASE=mcr.microsoft.com/dotnet/runtime-deps:10.0.13-noble-chiseled-amd64@sha256:e6cb0d241bab6f29daf92f2e11b3e605e0b0df4face98a71811c084aafa45593

ARG REDIS_VERSION=8.2.10
ARG REDIS_SOURCE_SHA256=d33935732f7fc15476295fe05f5ce740927bc14847798e47b3f67b4f27b8b478
ARG REDIS_VERSION_LINE=8.2
ARG REDIS_ARTIFACT_ID=IHL-CTR-0007
ARG REDIS_LICENSES=AGPL-3.0-only

FROM ${REDIS_BUILDER} AS openssl-supported-base-build
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


FROM ${REDIS_BUILDER} AS redis-build
ARG REDIS_VERSION
ARG REDIS_SOURCE_SHA256
ARG REDIS_VERSION_LINE
ARG REDIS_ARTIFACT_ID
COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl
ADD --checksum=sha256:${REDIS_SOURCE_SHA256} https://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz /tmp/redis.tar.gz
COPY images/redis/config/redis.secure.conf /tmp/redis.secure.conf
RUN set -eu; \
    printf '%s  %s\n' "$REDIS_SOURCE_SHA256" /tmp/redis.tar.gz | sha256sum --check --strict; \
    [ "${REDIS_VERSION%.*}" = "$REDIS_VERSION_LINE" ]; \
    case "$REDIS_ARTIFACT_ID" in IHL-CTR-[0-9][0-9][0-9][0-9]) ;; *) exit 1 ;; esac; \
    tar -xzf /tmp/redis.tar.gz -C /tmp; \
    cd "/tmp/redis-$REDIS_VERSION"; \
    make -C src -j2 redis-server redis-cli BUILD_TLS=yes USE_SYSTEMD=no MALLOC=libc OPENSSL_PREFIX=/opt/openssl \
      OPTIMIZATION=-O2 CFLAGS='-fstack-protector-strong -D_FORTIFY_SOURCE=2 -fPIE' \
      LDFLAGS='-pie -Wl,-z,relro,-z,now -Wl,-rpath,/opt/openssl/lib'; \
    install -d -m 0755 /out/opt/redis/bin /out/opt/redis/licenses /out/opt/ihl/redis; \
    install -m 0755 src/redis-server src/redis-cli /out/opt/redis/bin/; \
    for notice in LICENSE* COPYING*; do [ ! -f "$notice" ] || cp "$notice" /out/opt/redis/licenses/; done; \
    redis_version="$(LD_LIBRARY_PATH=/opt/openssl/lib src/redis-server --version)"; \
    case "$redis_version" in "Redis server v=$REDIS_VERSION "*) ;; *) exit 1 ;; esac; \
    ldd src/redis-server > /tmp/redis-linkage.txt; \
    ! grep -F 'not found' /tmp/redis-linkage.txt; \
    grep -F '/opt/openssl/lib/libssl.so.3' /tmp/redis-linkage.txt; \
    grep -F '/opt/openssl/lib/libcrypto.so.3' /tmp/redis-linkage.txt; \
    cp /tmp/redis.secure.conf /out/opt/ihl/redis/redis.conf; \
    if [ "$REDIS_VERSION_LINE" = "6.2" ]; then \
      sed -i '/^enable-protected-configs /d; /^enable-debug-command /d; /^enable-module-command /d' /out/opt/ihl/redis/redis.conf; \
    fi; \
    chmod 0444 /out/opt/ihl/redis/redis.conf; \
    install -d -m 0700 -o 1654 -g 1654 /out/data; \
    install -d -m 0755 /out/run/redis-secrets

FROM ${REDIS_BASE}
ARG REDIS_VERSION
ARG REDIS_VERSION_LINE
ARG REDIS_ARTIFACT_ID
ARG REDIS_LICENSES
ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
LABEL org.opencontainers.image.title="Indian Hill Redis ${REDIS_VERSION_LINE}" \
      org.opencontainers.image.version="${REDIS_VERSION}" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      org.opencontainers.image.licenses="${REDIS_LICENSES}" \
      com.indianhilllabs.artifact.id="${REDIS_ARTIFACT_ID}" \
      com.indianhilllabs.assurance.level="secure"
COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl
COPY --from=redis-build /out/ /
ENV LD_LIBRARY_PATH="/opt/openssl/lib" TZ="UTC" IHL_ASSURANCE_LEVEL="secure"
USER 1654:1654
WORKDIR /data
EXPOSE 6379
ENTRYPOINT ["/opt/redis/bin/redis-server", "/opt/ihl/redis/redis.conf"]
STOPSIGNAL SIGTERM

LABEL com.indianhilllabs.artifact.role="production"
