# The SDK exists only in this disposable build stage. It never becomes part of
# the final application image.
ARG SDK_BASE=mcr.microsoft.com/dotnet/sdk:8.0.426-noble-amd64@sha256:5c580c9ef8111b2677c6e75e5173f8cf8b36ec63c7ff06c8cf5e1d272e237aa2
ARG RUNTIME_BASE=ihl/aspnet-runtime:8.0.32-secure-lab.1
ARG ASSURANCE_LEVEL=secure
FROM ${SDK_BASE} AS build
WORKDIR /src

COPY images/aspnet/examples/reference-api/Ihl.ReferenceApi.csproj ./
COPY images/aspnet/examples/reference-api/NuGet.Config ./
RUN dotnet restore Ihl.ReferenceApi.csproj --configfile NuGet.Config /p:TargetFramework=net8.0

COPY images/aspnet/examples/reference-api/Program.cs ./
RUN dotnet publish Ihl.ReferenceApi.csproj \
    --disable-build-servers \
    --configuration Release \
    --no-restore \
    --output /out \
    /p:UseAppHost=false \
    /p:TargetFramework=net8.0

# The manual build uses the local default. CI overrides this with the exact
# digest produced by the runtime-image build in the same pipeline.
FROM ${RUNTIME_BASE}

ARG OCI_SOURCE="https://gitlab.com/indianhilllabs/indian-hill-secure-containers"
ARG OCI_REVISION="manual-build"
ARG OCI_CREATED="1970-01-01T00:00:00Z"
ARG ASSURANCE_LEVEL

LABEL org.opencontainers.image.title="IHL-CTR-0012 Reference API" \
      org.opencontainers.image.description="Validation consumer for an Indian Hill ASP.NET 8 Runtime variant" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      com.indianhilllabs.assurance.level="${ASSURANCE_LEVEL}"

COPY --from=build --chown=1654:1654 /out/ ./
CMD ["Ihl.ReferenceApi.dll"]

LABEL com.indianhilllabs.artifact.role="reference-application"
