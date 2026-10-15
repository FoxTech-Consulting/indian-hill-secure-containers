# NGINX is compiled from the checksum-pinned upstream source and linked to a
# separately controlled OpenSSL runtime. The final image begins from the
# Ubuntu 24.04 Chiseled runtime-deps base so it contains no package manager,
# compiler, shell entrypoint, or dynamic NGINX modules.
ARG NGINX_BUILDER=docker.io/library/gcc:11.2.0@sha256:2c5cae6b84598eb6865d6c7b340deef80e8834a4c4037a5cbba755a5258809d4
ARG NGINX_BASE=mcr.microsoft.com/dotnet/runtime-deps:10.0.13-noble-chiseled-amd64@sha256:e6cb0d241bab6f29daf92f2e11b3e605e0b0df4face98a71811c084aafa45593
FROM ${NGINX_BUILDER} AS openssl-supported-base-build

ARG NGINX_BUILDER
ARG OPENSSL_BASE_VERSION=3.5.9
ARG OPENSSL_BASE_SOURCE_SHA256=603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a

ADD --checksum=sha256:603f5602e2eef00d77fbd429d34dcd5822bb301757a1bc9cdb24c670f1eb859a \
    https://www.openssl.org/source/openssl-3.5.9.tar.gz \
    /tmp/openssl-3.5.9.tar.gz

RUN set -eu; \
    run_logged() { \
      log="$1"; shift; \
      if ! "$@" >"$log" 2>&1; then \
        printf 'ERROR: OpenSSL build command failed: %s\\n' "$*" >&2; \
        tail -n 250 "$log" >&2; \
        exit 1; \
      fi; \
    }; \
    printf '%s  %s\n' "$OPENSSL_BASE_SOURCE_SHA256" /tmp/openssl-3.5.9.tar.gz \
      | sha256sum --check --strict; \
    tar --extract --gzip --file /tmp/openssl-3.5.9.tar.gz --directory /tmp; \
    cd "/tmp/openssl-$OPENSSL_BASE_VERSION"; \
    run_logged /tmp/openssl-base-configure.log ./Configure \
      no-fips \
      --prefix=/opt/openssl \
      --openssldir=/opt/openssl/ssl \
      --libdir=lib; \
    run_logged /tmp/openssl-base-build.log make -j2; \
    run_logged /tmp/openssl-base-install.log make install_sw install_ssldirs; \
    install -d -m 0755 /opt/openssl/share/licenses/openssl; \
    install -m 0644 LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt; \
    printf 'OpenSSL base library %s build and installation completed.\n' "$OPENSSL_BASE_VERSION"

FROM ${NGINX_BUILDER} AS nginx-build

ARG NGINX_VERSION=1.30.4
ARG NGINX_SOURCE_SHA256=4261dc90e9e47c1c4041276e9aaa3d48ebe2e664f728e14fa95ae6c67d57a08b

COPY --from=openssl-supported-base-build /opt/openssl /opt/openssl

# The source checksum was calculated from the official nginx.org stable
# release archive. The source build deliberately omits dynamic modules, PCRE
# rewrite support, and gzip to keep the reusable server platform small.
ADD --checksum=sha256:4261dc90e9e47c1c4041276e9aaa3d48ebe2e664f728e14fa95ae6c67d57a08b \
    https://nginx.org/download/nginx-1.30.4.tar.gz \
    /tmp/nginx-1.30.4.tar.gz

RUN set -eu; \
    run_logged() { \
      log="$1"; shift; \
      if ! "$@" >"$log" 2>&1; then \
        printf 'ERROR: NGINX build command failed: %s\\n' "$*" >&2; \
        tail -n 250 "$log" >&2; \
        exit 1; \
      fi; \
    }; \
    printf '%s  %s\n' "$NGINX_SOURCE_SHA256" /tmp/nginx-1.30.4.tar.gz \
      | sha256sum --check --strict; \
    tar --extract --gzip --file /tmp/nginx-1.30.4.tar.gz --directory /tmp; \
    cd "/tmp/nginx-$NGINX_VERSION"; \
    run_logged /tmp/nginx-configure.log ./configure \
      --prefix=/usr/share/nginx \
      --sbin-path=/usr/sbin/nginx \
      --conf-path=/etc/nginx/nginx.conf \
      --pid-path=/tmp/nginx.pid \
      --error-log-path=/dev/stderr \
      --http-log-path=/dev/stdout \
      --http-client-body-temp-path=/tmp/nginx-client-body \
      --http-proxy-temp-path=/tmp/nginx-proxy \
      --http-fastcgi-temp-path=/tmp/nginx-fastcgi \
      --http-scgi-temp-path=/tmp/nginx-scgi \
      --http-uwsgi-temp-path=/tmp/nginx-uwsgi \
      --with-http_ssl_module \
      --without-http_rewrite_module \
      --without-http_auth_basic_module \
      --without-http_gzip_module \
      --without-pcre \
      --without-pcre2 \
      --with-cc-opt='-O2 -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=2 -I/opt/openssl/include' \
      --with-ld-opt='-Wl,-z,relro,-z,now -Wl,-rpath,/opt/openssl/lib -L/opt/openssl/lib'; \
    run_logged /tmp/nginx-build.log make -j2; \
    run_logged /tmp/nginx-install.log make install; \
    ldd /usr/sbin/nginx > /tmp/nginx-linkage.txt; \
    ! grep -F 'not found' /tmp/nginx-linkage.txt; \
    ! grep -F 'libcrypt.so.1' /tmp/nginx-linkage.txt; \
    grep -F '/opt/openssl/lib/libssl.so.3' /tmp/nginx-linkage.txt; \
    grep -F '/opt/openssl/lib/libcrypto.so.3' /tmp/nginx-linkage.txt; \
    printf 'NGINX %s build completed and is linked to /opt/openssl.\n' "$NGINX_VERSION"

FROM ${NGINX_BASE}

ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"

LABEL org.opencontainers.image.title="Indian Hill Secure NGINX 1.30" \
      org.opencontainers.image.description="Minimal non-root NGINX 1.30 server linked to a controlled OpenSSL 3.5.9 base library" \
      org.opencontainers.image.version="1.30.4-secure-lab.1" \
      org.opencontainers.image.vendor="Indian Hill Labs" \
      org.opencontainers.image.licenses="BSD-2-Clause AND Apache-2.0" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="IHL-CTR-0002" \
      com.indianhilllabs.standard="IHL-SCS-001-v0.1-draft" \
      com.indianhilllabs.assurance.level="secure"

COPY --from=nginx-build /usr/sbin/nginx /usr/sbin/nginx
COPY --from=nginx-build /opt/openssl/lib/libcrypto.so.3 /opt/openssl/lib/libcrypto.so.3
COPY --from=nginx-build /opt/openssl/lib/libssl.so.3 /opt/openssl/lib/libssl.so.3
COPY --from=nginx-build /opt/openssl/share/licenses/openssl/LICENSE.txt /opt/openssl/share/licenses/openssl/LICENSE.txt
COPY images/nginx/config/nginx.secure.conf /etc/nginx/nginx.conf
COPY images/nginx/config/health/secure.json /usr/share/nginx/html/healthz.json

ENV IHL_ASSURANCE_LEVEL="secure" \
    LD_LIBRARY_PATH="/opt/openssl/lib"

USER 1654:1654
WORKDIR /usr/share/nginx/html
EXPOSE 8080
ENTRYPOINT ["/usr/sbin/nginx"]
CMD ["-g", "daemon off;"]
STOPSIGNAL SIGQUIT

LABEL com.indianhilllabs.artifact.role="production"
