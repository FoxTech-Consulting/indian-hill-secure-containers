# This standard-library Node.js service is a test consumer for the reusable
# runtime. It adds no package manager, shell, native addon, or third-party
# dependency to the selected tier image.
ARG RUNTIME_BASE=ihl/node:24.20.0-secure-lab.1
ARG ASSURANCE_LEVEL=secure
FROM ${RUNTIME_BASE}

ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
ARG ASSURANCE_LEVEL

LABEL org.opencontainers.image.title="IHL-CTR-0005 Node.js Reference API" \
      org.opencontainers.image.description="Validation consumer for an Indian Hill Node.js 24 Runtime variant" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.assurance.level="${ASSURANCE_LEVEL}"

COPY --chown=1654:1654 images/node/examples/reference-api/server.js /app/server.js

USER 1654:1654
WORKDIR /app
EXPOSE 8080
CMD ["server.js"]

LABEL com.indianhilllabs.artifact.role="reference-application"
