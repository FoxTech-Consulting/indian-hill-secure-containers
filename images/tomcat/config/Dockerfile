# Temurin release metadata: https://api.adoptium.net/v3/assets/latest/21/hotspot
# This builder is discarded; the shipped runtime has no shell or compiler.
ARG JAVA_BUILDER=docker.io/library/gcc:11.2.0@sha256:2c5cae6b84598eb6865d6c7b340deef80e8834a4c4037a5cbba755a5258809d4
ARG JAVA_BASE=mcr.microsoft.com/dotnet/runtime-deps:10.0.13-noble-chiseled-amd64@sha256:e6cb0d241bab6f29daf92f2e11b3e605e0b0df4face98a71811c084aafa45593
FROM ${JAVA_BUILDER} AS java-build
ADD --checksum=sha256:ce79869e1307ed8ee1e2baa86a412b1eb5b75d10a01006d788a6f968bcfaee94 https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_x64_linux_hotspot_21.0.12.1_1.tar.gz /tmp/jdk.tar.gz
RUN mkdir /opt/jdk && tar -xzf /tmp/jdk.tar.gz --strip-components=1 -C /opt/jdk \
    && /opt/jdk/bin/jlink --add-modules java.base,java.logging,java.naming,java.management,java.sql,java.xml,java.net.http,jdk.httpserver,jdk.crypto.ec,jdk.unsupported,jdk.security.auth,java.desktop,java.instrument,java.rmi,java.security.jgss,jdk.management,jdk.zipfs,jdk.naming.dns \
       --strip-debug --no-header-files --no-man-pages --output /opt/java \
    && /opt/java/bin/java --version


ADD https://archive.apache.org/dist/tomcat/tomcat-10/v10.1.59/bin/apache-tomcat-10.1.59.tar.gz /tmp/tomcat.tar.gz
RUN echo '992a8e88fc9c0338445f018a1e4a2757c9e71708dba795e2864c9b1613f2b3b9b19c048e787682deae6d6bff9971defc746e31282085d52ef1d32192e09f7a0f  /tmp/tomcat.tar.gz' | sha512sum -c - \
    && mkdir -p /opt/tomcat && tar -xzf /tmp/tomcat.tar.gz --strip-components=1 -C /opt/tomcat \
    && rm -rf /opt/tomcat/webapps/* /opt/tomcat/bin/*.sh /opt/tomcat/bin/*.bat /opt/tomcat/bin/*.tar.gz \
    && mkdir -p /opt/tomcat/webapps /opt/tomcat/health /opt/tomcat/conf/Catalina/localhost
COPY images/tomcat/config/HealthCheck.java /tmp/
RUN /opt/jdk/bin/javac --release 21 -d /opt/tomcat/health /tmp/HealthCheck.java \
    && chmod -R a+rX /opt/tomcat \
    && chown 1654:1654 /opt/tomcat/work /opt/tomcat/temp

FROM ${JAVA_BASE}
ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
LABEL org.opencontainers.image.title="Indian Hill Apache Tomcat 10.1 Platform" \
      org.opencontainers.image.version="10.1.59" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      org.opencontainers.image.licenses="Apache-2.0 AND GPL-2.0-with-classpath-exception" \
      com.indianhilllabs.artifact.id="IHL-CTR-0008" \
      com.indianhilllabs.assurance.level="secure"
COPY --from=java-build /opt/java /opt/java
COPY --from=java-build /opt/tomcat /opt/tomcat
COPY images/tomcat/config/server.xml images/tomcat/config/context.xml images/tomcat/config/logging.properties /opt/tomcat/conf/
ENV JAVA_HOME="/opt/java" PATH="/opt/java/bin" IHL_ASSURANCE_LEVEL="secure" \
    CATALINA_HOME="/opt/tomcat" CATALINA_BASE="/opt/tomcat"
USER 1654:1654
WORKDIR /opt/tomcat
EXPOSE 8080
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 CMD ["/opt/java/bin/java", "-cp", "/opt/tomcat/health", "HealthCheck"]
ENTRYPOINT ["/opt/java/bin/java", "-Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager", "-Djava.util.logging.config.file=/opt/tomcat/conf/logging.properties", "-Dcatalina.home=/opt/tomcat", "-Dcatalina.base=/opt/tomcat", "-Djava.io.tmpdir=/tmp", "-cp", "/opt/tomcat/bin/bootstrap.jar:/opt/tomcat/bin/tomcat-juli.jar", "org.apache.catalina.startup.Bootstrap"]
CMD ["start"]

LABEL com.indianhilllabs.artifact.role="production"
