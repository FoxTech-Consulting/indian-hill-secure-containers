# Indian Hill Labs Secure Containers

Public source snapshots for Indian Hill Labs Secure and Hardened container engineering previews. The nine families are ASP.NET, NGINX, Python, PostgreSQL, Node.js, Java, Redis, Apache Tomcat, and Elasticsearch. The catalog includes each selected Java version and provider variant as an exact build target. Go's separate bare-image pipeline is outside this initial Secure/Hardened source snapshot.

**These sources are engineering previews. A successful local build does not qualify an image as Secure or Hardened and does not create a supported, generally available release.** The tier names describe the build definitions. Qualification requires the authoritative GitLab factory's exact digest, policy, tests, and retained evidence. No Validated sources or qualification workflows are included here.

## Source and image distribution

The [Indian Hill Labs container program](https://indianhilllabs.com/containers/)
provides the current program overview. This repository supplies source snapshots,
download records, and technical instructions.

GitLab remains the authoritative build and qualification system. This repository contains a reviewed subset of its build sources, configuration, and examples; private platform operations and dashboards are excluded. `SOURCE.json` records the full GitLab source revision and the SHA-256 of each exported file. A public `source-<40-character-GitLab-revision>` tag identifies that snapshot. The GitHub snapshot commit is a separate Git commit and will have a different SHA.

`public-products.json` lists the exact versions and build paths in this snapshot. Current sources target **Linux on AMD64 (`linux/amd64`)**. They do not establish ARM64 support. Java's private qualification sample is omitted; its runtime sources remain available.

Prebuilt images, when published, are distributed through GitHub Container Registry. A source snapshot or a proposed registry name is not evidence that a package is available. Use only a published release or preview record that supplies all of the following:

- the public image location and immutable `sha256` digest;
- its preview or release status, tier, version, and supported platform;
- the exact GitLab source revision and assurance-manifest SHA-256;
- SBOM, vulnerability findings, provenance, and qualification evidence locations and access requirements; and
- signature-verification instructions and known usage constraints.

Runtime images and companion test images have separate access settings. A publicly accessible runtime does not establish anonymous access to its companion image; follow the published package record for any authentication requirement.

Image tags include timestamps; determine whether an image is a preview or a release from its publication record. Public availability does not establish release status. No generally available release is declared by this README. Inspect published findings before choosing a preview: the Secure factory reports unresolved vulnerabilities without making every finding a publication blocker. Hardened has additional assessment gates. Neither name means vulnerability-free or certifies an entire deployment.

## Download a prebuilt image

[published-images.json](published-images.json) lists the runtime images whose exact digests passed an anonymous download check. Each entry records its tier, version, original GitLab source revision, publication job, and the time and scope of that check. These are **engineering previews for Linux on AMD64**. Check the recorded version and findings before using one; publication does not confer general availability, FIPS validation, or qualification of your deployment.

For example, pull the verified NGINX previews by immutable digest:

```console
# Secure NGINX
docker pull --platform linux/amd64 ghcr.io/foxtech-consulting/nginx@sha256:a180c03a4ee59c8a4cb23e8775d3008d9fa42c91fb59e94d27925f9abb0dfc19

# Hardened NGINX
docker pull --platform linux/amd64 ghcr.io/foxtech-consulting/nginx@sha256:ffb5232b592ed35b3e60f47fce39a0d2a7e7623d6bacb78f193c6833878a0a24
```

Keep the `@sha256:...` digest when pinning an image in Docker Compose or Kubernetes. A timestamped tag is useful for discovery; the digest selects the exact artifact. The published image's source revision can differ from this README's `SOURCE.json`, because documentation and the download catalog can be updated independently of the image's original build.

<!-- BEGIN VERIFIED IMAGE TABLE -->
Verified download inventory updated **15 October 2026, 20:33 EDT (16 October, 00:33 UTC)**: **22 Secure and seven Hardened runtime previews**. No registry login was needed for these listed digests; individual download-check timestamps are recorded in the catalog.

Every repository below uses the prefix `ghcr.io/foxtech-consulting/`. Repository links open its GitHub package page. Copyable commands and full digests are in [published-images.json](published-images.json). Tags identify the exact listed versions; some previews predate newer source-build versions.

| Build key | Repository | Secure tag | Hardened tag |
| --- | --- | --- | --- |
| `aspnet` | [`aspnet`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/aspnet) | `IHL-ASPNet-10.0.13-20261016T002432Z` | `IHL-ASPNet-10.0.13-20261015T173239Z-Hardened` |
| `nginx` | [`nginx`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/nginx) | `IHL-NGINX-1.30.4-20261016T001214Z` | `IHL-NGINX-1.30.4-20261015T173635Z-Hardened` |
| `python` | [`python`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/python) | `IHL-Python-3.13.16-20261016T002718Z` | `IHL-Python-3.13.16-20261015T174218Z-Hardened` |
| `postgres` | [`postgres`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/postgres) | `IHL-Postgres-16.15-20261016T002606Z` | `IHL-Postgres-16.15-20261015T174531Z-Hardened` |
| `node` | [`node`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/node) | `IHL-Node-24.20.0-20261016T001723Z` | `IHL-Node-24.20.0-20261016T002924Z-Hardened` |
| `java` (Java 21 / bcfips-2-1-3) | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-21.0.12.1-20261010T221045Z` | `IHL-Java-21.0.12.1-20261015T024556Z-Hardened` |
| `redis` | [`redis`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/redis) | `IHL-Redis-8.2.9-20261016T003040Z` | Pending qualification |
| `tomcat` | [`tomcat`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/tomcat) | `IHL-Tomcat-10.1.59-20261016T002859Z` | `IHL-Tomcat-10.1.59-20261016T003116Z-Hardened` |
| `elasticsearch` | [`elasticsearch`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/elasticsearch) | `IHL-Elasticsearch-9.5.3-20261010T231254Z` | Not listed |
| `java-8-bcfips-2-1-1` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-8.0.504-20261010T221458Z` | Not listed |
| `java-8-bcfips-2-1-3` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-8.0.504-20261010T221631Z` | Not listed |
| `java-11-bcfips-2-1-1` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-11.0.32.1-20261010T221803Z` | Not listed |
| `java-11-bcfips-2-1-3` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-11.0.32.1-20261010T221932Z` | Not listed |
| `java-17-bcfips-2-1-1` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-17.0.20.1-20261010T222357Z` | Not listed |
| `java-17-bcfips-2-1-3` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-17.0.20.1-20261010T222713Z` | Not listed |
| `java-21-bcfips-2-1-1` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-21.0.12.1-20261010T223142Z` | Not listed |
| `java-25-bcfips-2-1-1` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-25.0.4.1-20261010T223358Z` | Not listed |
| `java-25-bcfips-2-1-3` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-25.0.4.1-20261010T223527Z` | Not listed |
| `java-26-bcfips-2-1-1` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-26.0.2.1-20261010T224015Z` | Not listed |
| `java-26-bcfips-2-1-3` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-26.0.2.1-20261010T224212Z` | Not listed |
| `java-27-bcfips-2-1-1` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-27-20261010T224344Z` | Not listed |
| `java-27-bcfips-2-1-3` | [`java`](https://github.com/orgs/FoxTech-Consulting/packages/container/package/java) | `IHL-Java-27-20261010T224518Z` | Not listed |

"Not listed" means this snapshot advertises no verified download for that tier. Redis Hardened is awaiting qualification. The Java provider names identify build targets and do not confer FIPS validation.

Fifteen Secure previews (the 14 Java targets and Elasticsearch) and the Java Hardened preview predate signed GitHub source bindings. The seven newer Secure previews and six other Hardened previews have bindings recorded in the catalog. Publication-only entries distinguish the image's original producer commit Q from the current publisher commit R. A newer source snapshot must not be substituted for a legacy image's original source.

Recorded vulnerability summaries are included where available. Download verification and tier labels do not imply zero findings. Signature provenance and missing legacy annotation values are disclosed separately from anonymous download checks.
<!-- END VERIFIED IMAGE TABLE -->

The table covers runtime images. Companion qualification images have separate visibility and are not required to download or build on a runtime. Source builds remain available for every target in `public-products.json`, including targets without a listed prebuilt image. Publication job links and retained qualification evidence can require GitLab access. Follow the signature checks below before trusting a downloaded preview.

## Build a local image

You need Python 3.10 or newer and Docker with BuildKit and Linux container support. Source builds download pinned upstream inputs and can take several minutes. Run commands from the repository root:

```console
python tools/build.py --list
python tools/build.py nginx --tier secure --dry-run
python tools/build.py nginx --tier secure
python tools/build.py nginx --tier hardened
python tools/build.py aspnet --tier hardened --with-example
python tools/build.py java-17-bcfips-2-1-1 --tier hardened --dry-run
```

The helper verifies this snapshot's exported file checksums before planning a build. Hardened builds first construct the local Secure parent, then use that invocation's uniquely tagged local parent. A registered example is built only with `--with-example`. All results use `local/ihl` tags and explicit `local-unqualified` metadata. The helper does not push, sign, scan, or qualify images. `--dry-run` prints argument arrays without contacting Docker or downloading anything.

For example, NGINX Secure builds to `local/ihl/nginx:<version>-secure-local`, where `<version>` comes from `public-products.json`. Override the local name prefix with `--tag-prefix`; this changes local names only. Dockerfiles use the repository root as their build context. Configuration may require mounted data, certificates, or secrets; examine the selected family's files before running it. Source builds are not promised to reproduce a published digest bit for bit.

Use the exact key printed by `--list` for Java version/provider variants. A provider variant name identifies its selected build target; it does not confer a FIPS qualification decision. Java reference examples are not included because they depend on the private qualification workload.

## Verify a published image

Use the exact image digest and signed annotations from the same publication record. `published-images.json` records signature-verification and public-source-binding status separately: an anonymous download check alone does not verify a signature. Publication job links or supporting evidence can require GitLab access.

Check every key and exact value in the selected record's `signatureVerification.signedAnnotations` with a separate `-a key=value` argument. When `signedAnnotationsComplete` is false, the catalog does not contain the complete signed values: obtain the original signed record from the linked publication job before verifying. Do not guess missing values from a tag or a newer source snapshot.

For an image with a verified public source binding, obtain its tier, original GitLab source revision, assurance-manifest hash, public source commit, source-manifest hash, publication context, and release registry from that record. The public source commit and GitLab revision identify separate histories. With a supported Cosign installation, substitute those values:

```console
cosign verify --certificate-oidc-issuer https://gitlab.com --certificate-identity https://gitlab.com/indianhilllabs/indian-hill-secure-containers//.gitlab-ci.yml@refs/heads/main -a assurance-tier=<signed-tier> -a source-revision=<signed-original-GitLab-revision> -a assurance-manifest-sha256=<signed-manifest-hash> -a public-source-commit=<signed-GitHub-commit> -a public-source-manifest-sha256=<signed-SOURCE-json-hash> -a publication-context=<signed-publication-context> -a release-registry=<signed-release-registry> <published-image>@sha256:<published-digest>
```

Older publications can lack the two `public-source-*` annotations. For a complete legacy GHCR record that contains the core qualification annotations, publication context, and release registry, verify all five recorded values:

```console
cosign verify --certificate-oidc-issuer https://gitlab.com --certificate-identity https://gitlab.com/indianhilllabs/indian-hill-secure-containers//.gitlab-ci.yml@refs/heads/main -a assurance-tier=<signed-tier> -a source-revision=<signed-original-GitLab-revision> -a assurance-manifest-sha256=<signed-manifest-hash> -a publication-context=<signed-publication-context> -a release-registry=<signed-release-registry> <published-image>@sha256:<published-digest>
```

Publication-only records can also include `publisher-revision`. When that key is present, add `-a publisher-revision=<signed-publisher-commit>` before the image argument in the applicable command. This is the publisher commit R; `source-revision` remains the image's original producer commit Q. Add an argument for every other recorded annotation as well. Only omit an example flag when the complete original signed record confirms that its key is absent; incomplete catalog entries do not establish absence.

The placeholders are intentional. Require the expected issuer, exact certificate identity, digest, and every annotation that the selected record claims. If a record has no verified public source binding, a valid legacy signature does not authenticate a GitHub source snapshot. Do not substitute this README's `SOURCE.json` or a newer source revision for the image's original source. Where a verified binding exists, authenticate the matching `SOURCE.json` checksum list against its signed source-manifest hash before verifying that snapshot's files.

Check the publication's provenance and available evidence against the same digest and source identities. An SBOM or a successful signature check alone does not establish qualification or deployment suitability.

Keep the selected digest in deployment configuration. Follow the image's non-root identity, drop unnecessary capabilities, set resource limits, and mount only required data and secrets. Review whether the application supports a read-only root filesystem. Host, runtime, orchestration, and operational controls remain part of your deployment.

## Contribute and report security issues

See [CONTRIBUTING.md](CONTRIBUTING.md) for proposed changes and [SECURITY.md](SECURITY.md) for confidential reporting. Pull requests are proposals reviewed by the authoritative GitLab project; merging a GitHub proposal does not bypass the GitLab qualification or publication process.

## License

Indian Hill Labs' original code and configuration in this snapshot are licensed under [Apache License 2.0](LICENSE), except where a file carries a different notice. [NOTICE](NOTICE) explains the scope. Upstream software, base images, libraries, and their notices retain their own licenses. In particular, the Redis recipe selects AGPLv3, Java includes GPLv2 with the Classpath Exception components, and the Elasticsearch recipe uses a vendor-distributed image whose terms must be checked independently. Apache-2.0 does not relicense those components. Preserve applicable notices and meet the corresponding-source requirements when distributing your own images.
