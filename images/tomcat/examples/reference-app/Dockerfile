# The reference servlet is added only to the digest-pinned production runtime.
ARG RUNTIME_BASE
FROM ${RUNTIME_BASE} AS runtime
FROM docker.io/library/gcc:11.2.0@sha256:2c5cae6b84598eb6865d6c7b340deef80e8834a4c4037a5cbba755a5258809d4 AS compile
ADD --checksum=sha256:ce79869e1307ed8ee1e2baa86a412b1eb5b75d10a01006d788a6f968bcfaee94 https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_x64_linux_hotspot_21.0.12.1_1.tar.gz /tmp/jdk.tar.gz
RUN mkdir /opt/jdk && tar -xzf /tmp/jdk.tar.gz --strip-components=1 -C /opt/jdk
COPY --from=runtime /opt/tomcat/lib/servlet-api.jar /tmp/servlet-api.jar
COPY images/tomcat/examples/reference-app/HealthServlet.java /tmp/HealthServlet.java
RUN mkdir /classes && /opt/jdk/bin/javac --release 21 -cp /tmp/servlet-api.jar -d /classes /tmp/HealthServlet.java
FROM runtime
ARG ASSURANCE_LEVEL=secure
ARG OCI_REVISION="manual-build"
LABEL com.indianhilllabs.artifact.id="IHL-APP-0006" \
      com.indianhilllabs.artifact.role="reference-application" \
      com.indianhilllabs.assurance.level="${ASSURANCE_LEVEL}" \
      org.opencontainers.image.revision="${OCI_REVISION}"
COPY --from=compile --chown=0:0 /classes /opt/tomcat/webapps/ROOT/WEB-INF/classes
COPY --chmod=0444 images/tomcat/examples/reference-app/health-web.xml /opt/tomcat/webapps/ROOT/WEB-INF/web.xml
USER 1654:1654
