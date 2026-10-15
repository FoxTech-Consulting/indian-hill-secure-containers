# A digest pin makes the input immutable. The readable tag documents what the
# digest represented when this lab build was authored.
ARG ASPNET_BASE=mcr.microsoft.com/dotnet/aspnet:10.0.13-noble-chiseled-amd64@sha256:f9d8d2664e0a80931b3db97401824b0721819eedee54aeda15bf8bb7a4306738
FROM ${ASPNET_BASE}

ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"

LABEL org.opencontainers.image.title="Indian Hill Secure ASP.NET 10 Runtime" \
      org.opencontainers.image.description="Minimal Secure-level ASP.NET 10 runtime candidate" \
      org.opencontainers.image.version="10.0.13-secure-lab.1" \
      org.opencontainers.image.vendor="Indian Hill Labs" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="IHL-CTR-0001" \
      com.indianhilllabs.standard="IHL-SCS-001-v0.1-draft" \
      com.indianhilllabs.assurance.level="secure"

ENV IHL_ASSURANCE_LEVEL="secure"

# Chiseled already declares UID 1654. Repeating it here makes the IHL runtime
# contract explicit and supplies a numeric group even if a caller changes name
# resolution behavior.
USER 1654:1654
WORKDIR /app

# EXPOSE is documentation in image metadata; it does not publish a host port.
EXPOSE 8080

# Exec-form startup avoids an intermediate shell and preserves signal delivery.
ENTRYPOINT ["/usr/bin/dotnet"]
CMD ["--info"]
STOPSIGNAL SIGTERM

LABEL com.indianhilllabs.artifact.role="production"
