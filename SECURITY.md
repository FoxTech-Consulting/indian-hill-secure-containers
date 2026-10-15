# Security policy

This repository publishes source snapshots for engineering previews. A snapshot is not a generally available release or a commitment to support every listed upstream version. Each published image's release record must identify its maintenance status, supported platform, exact digest, and known findings. Until such a record is available, treat the sources and any candidate images as previews without a production support commitment.

## Report a vulnerability privately

Do not put credentials, exploit details, or other sensitive information in a public issue or pull request.

Private vulnerability reporting is enabled for this GitHub repository. Use **Security → Advisories → Report a vulnerability**, or open:

<https://github.com/foxtech-consulting/indian-hill-secure-containers/security/advisories/new>

If the action is temporarily unavailable, keep the details private. A maintainer with access to the authoritative GitLab project can submit a **confidential** issue there after confirming the confidential flag and its access restrictions. Do not use an ordinary GitHub or GitLab issue as a substitute. No public email address or alternative intake endpoint is declared here.

Include the image digest or source snapshot revision, affected version, configuration, expected and observed behavior, impact, and minimal reproduction steps. Remove secrets and personal information from logs. Identify whether the report concerns these build sources, an upstream component, or deployment configuration, if known.

Maintainers will triage actionable reports, investigate the exact affected artifact, and coordinate fixes and disclosure. A corrected source snapshot is not a fixed image: the authoritative GitLab factory must rebuild, reassess, and publish a replacement digest. No acknowledgement deadline, bounty, or service-level agreement is promised by this policy.
