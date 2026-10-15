# Contributing

Thank you for helping improve Indian Hill Labs container sources. This GitHub repository is a curated public source view. GitLab remains authoritative for changes, image builds, qualification, signatures, and publication.

## Propose a change

For a non-sensitive bug or feature, open an issue or pull request with the affected family, snapshot tag, expected behavior, and a small reproduction. Include the upstream version and image digest when relevant. Follow [SECURITY.md](SECURITY.md) for vulnerabilities; do not disclose sensitive findings in ordinary issues.

Keep proposals focused on Secure/Hardened build sources, configuration, local build usability, or examples. Do not add credentials, internal infrastructure, private operations, downloaded vendor binaries, or Validated/FIPS qualification workflows to this public source view.

Preserve upstream notices, checksum pins, non-root runtime behavior, and existing controls. Explain a proposed control change and its effects rather than silently disabling a check. Changing an upstream version requires reviewing its source checksum, license, runtime behavior, and vulnerability implications. Include tests or a reproducible check that exercises the changed behavior when appropriate.

## Check a local build

```console
python tools/build.py --list
python tools/build.py nginx --tier hardened --dry-run
python tools/build.py nginx --tier hardened
```

Use the relevant family in place of `nginx`. The local helper verifies the snapshot checksums, so an intentional source edit requires checking and rebuilding directly with Docker or regenerating a new reviewed snapshot through the authoritative export process. Do not edit `SOURCE.json` to present modified files as the original snapshot. Explain local modifications and the exact Docker command in your proposal. Local builds are unqualified; they do not replace GitLab's tests or evidence.

## Review and publication

Maintainers review GitHub proposals and carry accepted changes into the authoritative GitLab project. Qualified changes return as a fresh exported snapshot; private build history and operational files are not mirrored. A pull request or source tag does not publish an image. Registry publication still follows protected GitLab jobs and their evidence gates.

By submitting original contributions intended for inclusion here, you agree that they may be distributed under Apache License 2.0, as described in [LICENSE](LICENSE) and [NOTICE](NOTICE). Identify third-party material and its license explicitly; do not submit code you cannot license on those terms. No contributor license agreement or DCO sign-off requirement is established by this file.
