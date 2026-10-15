ARG REDIS_BUILDER=docker.io/library/gcc:11.2.0@sha256:2c5cae6b84598eb6865d6c7b340deef80e8834a4c4037a5cbba755a5258809d4
ARG REDIS_BASE=mcr.microsoft.com/dotnet/runtime-deps:10.0.13-noble-chiseled-amd64@sha256:e6cb0d241bab6f29daf92f2e11b3e605e0b0df4face98a71811c084aafa45593

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
COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl
ADD --checksum=sha256:531b314e5557ad76d941f605b3e3162ac61dc141f37c407e1f91fcfe17ea8c30 https://download.redis.io/releases/redis-8.2.9.tar.gz /tmp/redis.tar.gz
RUN set -eu; \
    tar -xzf /tmp/redis.tar.gz -C /tmp; \
    cd /tmp/redis-8.2.9; \
    make -j2 BUILD_TLS=yes USE_SYSTEMD=no MALLOC=libc OPENSSL_PREFIX=/opt/openssl \
      OPTIMIZATION=-O2 CFLAGS='-fstack-protector-strong -D_FORTIFY_SOURCE=2 -fPIE' \
      LDFLAGS='-pie -Wl,-z,relro,-z,now -Wl,-rpath,/opt/openssl/lib'; \
    install -d -m 0755 /out/opt/redis/bin /out/opt/redis/licenses /out/opt/ihl/redis; \
    install -m 0755 src/redis-server src/redis-cli /out/opt/redis/bin/; \
    cp LICENSE* /out/opt/redis/licenses/; \
    install -d -m 0700 -o 1654 -g 1654 /out/data; \
    install -d -m 0755 /out/run/redis-secrets

FROM ${REDIS_BASE}
ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
LABEL org.opencontainers.image.title="Indian Hill Redis Open Source 8.2" \
      org.opencontainers.image.version="8.2.9" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      org.opencontainers.image.licenses="AGPL-3.0-only" \
      com.indianhilllabs.artifact.id="IHL-CTR-0007" \
      com.indianhilllabs.assurance.level="secure"
COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl
COPY --from=redis-build /out/ /
COPY --chmod=0444 images/redis/config/redis.secure.conf /opt/ihl/redis/redis.conf
ENV LD_LIBRARY_PATH="/opt/openssl/lib" TZ="UTC" IHL_ASSURANCE_LEVEL="secure"
USER 1654:1654
WORKDIR /data
EXPOSE 6379
ENTRYPOINT ["/opt/redis/bin/redis-server", "/opt/ihl/redis/redis.conf"]
STOPSIGNAL SIGTERM

LABEL com.indianhilllabs.artifact.role="production"
