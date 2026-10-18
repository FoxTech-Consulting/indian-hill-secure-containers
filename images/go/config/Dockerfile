# Only data needed by statically linked Go applications is carried into the base.
# The compiler and every application executable are supplied separately.
FROM mcr.microsoft.com/dotnet/runtime-deps:10.0.11-noble-chiseled-amd64@sha256:854aabebc630c23bfc0d67c09f06dda4fbce8a846ae6e040f4b2a382bb3c4653 AS trust
FROM scratch
ARG GO_PRODUCT_VERSION=1.27.2
ARG GO_ARTIFACT_ID=IHL-CTR-0010
ARG OCI_REVISION
ARG OCI_CREATED
LABEL org.opencontainers.image.title="Indian Hill Go Static Runtime Base" \
      org.opencontainers.image.version="${GO_PRODUCT_VERSION}" \
      org.opencontainers.image.source="https://gitlab.com/indianhilllabs/indian-hill-secure-containers" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="${GO_ARTIFACT_ID}" \
      com.indianhilllabs.artifact.role="runtime-base" \
      com.indianhilllabs.application.included="false" \
      com.indianhilllabs.release.status="candidate" \
      com.indianhilllabs.assurance.level="secure"
COPY --from=trust /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=trust /etc/passwd /etc/passwd
COPY --from=trust /etc/group /etc/group
ENV IHL_ASSURANCE_LEVEL="secure"
USER 1654:1654
WORKDIR /app
