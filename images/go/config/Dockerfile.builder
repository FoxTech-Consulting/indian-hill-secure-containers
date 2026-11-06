# Separate build tool. No customer or reference application is bundled.
ARG GO_COMPILER=docker.io/library/golang:1.27.3-bookworm@sha256:d9b6a1beb9474adc2a1ce842573639b44b2a0dd49b6669f51d3821baf9ec37c9
FROM ${GO_COMPILER} AS compiler
FROM mcr.microsoft.com/dotnet/runtime-deps:10.0.11-noble-chiseled-amd64@sha256:854aabebc630c23bfc0d67c09f06dda4fbce8a846ae6e040f4b2a382bb3c4653 AS trust
FROM scratch
ARG GO_PRODUCT_VERSION=1.27.3
ARG OCI_REVISION
ARG OCI_CREATED
COPY --from=compiler /usr/local/go /usr/local/go
COPY --from=trust /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=trust /etc/passwd /etc/passwd
COPY --from=trust /etc/group /etc/group
LABEL org.opencontainers.image.title="Indian Hill Go ${GO_PRODUCT_VERSION} Build Environment" \
      org.opencontainers.image.version="${GO_PRODUCT_VERSION}" \
      org.opencontainers.image.source="https://gitlab.com/indianhilllabs/indian-hill-secure-containers" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.role="build-tool" \
      com.indianhilllabs.application.included="false" \
      com.indianhilllabs.release.status="candidate"
ENV GOTOOLCHAIN="local" CGO_ENABLED="0" GOENV="off" \
    GOCACHE="/tmp/go-cache" GOMODCACHE="/tmp/go-mod" \
    GOROOT="/usr/local/go" PATH="/usr/local/go/bin" HOME="/tmp"
USER 1654:1654
WORKDIR /workspace
CMD ["go", "version"]
