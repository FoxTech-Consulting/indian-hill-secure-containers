# This minimal standard-library application is a test consumer for the
# reusable Python runtime. It adds no interpreter, package manager, shell, or
# third-party dependency to the selected assurance-tier base image.
ARG RUNTIME_BASE=ihl/python:3.13.18-secure-lab.1
ARG ASSURANCE_LEVEL=secure
FROM ${RUNTIME_BASE}

ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
ARG ASSURANCE_LEVEL
ARG PYTHON_VERSION=3.13.18
ARG PYTHON_VERSION_LINE=3.13
ARG PYTHON_ARTIFACT_ID=IHL-CTR-0003

LABEL org.opencontainers.image.title="Python ${PYTHON_VERSION} Reference API" \
      org.opencontainers.image.description="Validation consumer for an Indian Hill Python ${PYTHON_VERSION} Runtime variant" \
      org.opencontainers.image.version="${PYTHON_VERSION}-${ASSURANCE_LEVEL}" \
      com.indianhilllabs.artifact.runtime.id="${PYTHON_ARTIFACT_ID}" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.assurance.level="${ASSURANCE_LEVEL}"

COPY --chown=1654:1654 images/python/examples/reference-api/server.py /app/server.py

USER 1654:1654
WORKDIR /app
EXPOSE 8080
CMD ["/app/server.py"]

LABEL com.indianhilllabs.artifact.role="reference-application"
