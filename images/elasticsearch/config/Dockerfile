ARG ELASTICSEARCH_BASE=docker.elastic.co/elasticsearch/elasticsearch:9.5.5-amd64@sha256:c40a1fb2bc6976821e5625d2329992a1e9c29df576e5955fdcba02421abf0d3c
FROM ${ELASTICSEARCH_BASE}
ARG ELASTICSEARCH_VERSION=9.5.5
ARG ELASTICSEARCH_VERSION_LINE=9.5
ARG ELASTICSEARCH_ARTIFACT_ID=IHL-CTR-0009
ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
LABEL org.opencontainers.image.title="Indian Hill Elasticsearch ${ELASTICSEARCH_VERSION_LINE} Platform" \
      org.opencontainers.image.version="${ELASTICSEARCH_VERSION}" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="${ELASTICSEARCH_ARTIFACT_ID}" \
      com.indianhilllabs.assurance.level="secure"
# Keep the vendor JDK, native libraries, entrypoint and ECK tooling together.
COPY --chown=1000:0 --chmod=0660 images/elasticsearch/config/elasticsearch.secure.yml /usr/share/elasticsearch/config/elasticsearch.yml
ENV IHL_ASSURANCE_LEVEL="secure"
USER 1000:0
EXPOSE 9200 9300
STOPSIGNAL SIGTERM

LABEL com.indianhilllabs.artifact.role="production"
