ARG ELASTICSEARCH_BASE=docker.elastic.co/elasticsearch/elasticsearch:9.5.3-amd64@sha256:7b69d47de433699d6df59ef2d14d82d1b0f5a14ed48cf0244a6b20cc4222484e
FROM ${ELASTICSEARCH_BASE}
ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
LABEL org.opencontainers.image.title="Indian Hill Elasticsearch 9.5 Platform" \
      org.opencontainers.image.version="9.5.3" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.artifact.id="IHL-CTR-0009" \
      com.indianhilllabs.assurance.level="secure"
# Keep the vendor JDK, native libraries, entrypoint and ECK tooling together.
COPY --chown=1000:0 --chmod=0660 images/elasticsearch/config/elasticsearch.secure.yml /usr/share/elasticsearch/config/elasticsearch.yml
ENV IHL_ASSURANCE_LEVEL="secure"
USER 1000:0
EXPOSE 9200 9300
STOPSIGNAL SIGTERM

LABEL com.indianhilllabs.artifact.role="production"
