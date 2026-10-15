# Indian Hill Labs Secure Containers

Public source snapshots for Indian Hill Labs Secure and Hardened container engineering previews. The nine families are ASP.NET, NGINX, Python, PostgreSQL, Node.js, Java, Redis, Apache Tomcat, and Elasticsearch. The catalog includes each selected Java version and provider variant as an exact build target. Go's separate bare-image pipeline is outside this initial Secure/Hardened source snapshot.

**These sources are engineering previews. A successful local build does not qualify an image as Secure or Hardened and does not create a supported, generally available release.** The tier names describe the build definitions. Qualification requires the authoritative GitLab factory's exact digest, policy, tests, and retained evidence. No Validated sources or qualification workflows are included here.

## Source and image distribution

GitLab remains the authoritative build and qualification system. This repository contains a reviewed subset of its build sources, configuration, and examples; private platform operations and dashboards are excluded. `SOURCE.json` records the full GitLab source revision and the SHA-256 of each exported file. A public `source-<40-character-GitLab-revision>` tag identifies that snapshot. The GitHub snapshot commit is a separate Git commit and will have a different SHA.

`public-products.json` lists the exact versions and build paths in this snapshot. Current sources target **Linux on AMD64 (`linux/amd64`)**. They do not establish ARM64 support. Java's private qualification sample is omitted; its runtime sources remain available.

Prebuilt images, when published, are distributed through GitHub Container Registry. A source snapshot or a proposed registry name is not evidence that a package is available. Use only a published release or preview record that supplies all of the following:

- the public image location and immutable `sha256` digest;
- its preview or release status, tier, version, and supported platform;
- the exact GitLab source revision and assurance-manifest SHA-256;
- accessible SBOM, vulnerability findings, provenance, and qualification evidence; and
- signature-verification instructions and known usage constraints.

Runtime images and companion test images have separate access settings. A publicly accessible runtime does not establish anonymous access to its companion image; follow the published package record for any authentication requirement.

Image tags include timestamps; determine whether an image is a preview or a release from its publication record. Public availability does not establish release status. No generally available release is declared by this README. Inspect published findings before choosing a preview: the Secure factory reports unresolved vulnerabilities without making every finding a publication blocker. Hardened has additional assessment gates. Neither name means vulnerability-free or certifies an entire deployment.

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

Obtain the image digest, tier, GitLab source revision, assurance-manifest hash, public source commit, and source-manifest hash from the same approved preview or release record. The public source commit and GitLab revision identify separate histories. With a supported Cosign installation, substitute those published values in this example:

```console
cosign verify --certificate-oidc-issuer https://gitlab.com --certificate-identity https://gitlab.com/indianhilllabs/indian-hill-secure-containers//.gitlab-ci.yml@refs/heads/main -a assurance-tier=<secure-or-hardened> -a source-revision=<40-character-GitLab-revision> -a assurance-manifest-sha256=<64-character-manifest-hash> -a public-source-commit=<40-character-GitHub-commit> -a public-source-manifest-sha256=<64-character-SOURCE-json-hash> <published-image>@sha256:<published-digest>
```

The placeholders are intentional; this is not a download endpoint. Verify the destination image's signature, issuer, exact certificate identity, and all five annotations. Check the release's provenance and evidence against that same image digest, source revision, and manifest hashes. An SBOM or a successful signature check alone does not establish qualification or deployment suitability. Authenticate the `SOURCE.json` checksum list against the signed source-manifest hash before using it to verify the snapshot's files.

Keep the selected digest in deployment configuration. Follow the image's non-root identity, drop unnecessary capabilities, set resource limits, and mount only required data and secrets. Review whether the application supports a read-only root filesystem. Host, runtime, orchestration, and operational controls remain part of your deployment.

## Contribute and report security issues

See [CONTRIBUTING.md](CONTRIBUTING.md) for proposed changes and [SECURITY.md](SECURITY.md) for confidential reporting. Pull requests are proposals reviewed by the authoritative GitLab project; merging a GitHub proposal does not bypass the GitLab qualification or publication process.

## License

Indian Hill Labs' original code and configuration in this snapshot are licensed under [Apache License 2.0](LICENSE), except where a file carries a different notice. [NOTICE](NOTICE) explains the scope. Upstream software, base images, libraries, and their notices retain their own licenses. In particular, the Redis recipe selects AGPLv3, Java includes GPLv2 with the Classpath Exception components, and the Elasticsearch recipe uses a vendor-distributed image whose terms must be checked independently. Apache-2.0 does not relicense those components. Preserve applicable notices and meet the corresponding-source requirements when distributing your own images.
