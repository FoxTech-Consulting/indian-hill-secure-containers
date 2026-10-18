#!/bin/sh
# Apply reviewed image-owned CIS filesystem settings; never remediate a host.
set -eu
[ "$(id -u)" = 0 ]
chmod 0644 /etc/passwd
# The fixed service identity owns its home. Runtime group 0 remains supported.
chown 1000:1000 /usr/share/elasticsearch
chmod 0750 /usr/share/elasticsearch
find /usr/share/elasticsearch -maxdepth 1 -type f -name '.*' -exec chown 1000:1000 {} +
find /usr/share/elasticsearch -maxdepth 1 -type f -name '.*' -exec chmod 0640 {} +
for file in /etc/bashrc /etc/bash.bashrc /etc/profile /etc/profile.d/*.sh; do
    [ -f "$file" ] || continue
    sed -i -E 's/(umask[[:space:]]+)[0-7]{3,4}/\1027/g' "$file"
done
for file in /etc/bashrc /etc/bash.bashrc /etc/profile; do
    [ -f "$file" ] || continue
    printf '\numask 027\n' >> "$file"
    cat >> "$file" <<'IHL_TIMEOUT'
# CIS Level 1 interactive-shell inactivity bound, safe when files are sourced twice.
case ${TMOUT-} in
    [1-9]|[1-9][0-9]|[1-8][0-9][0-9]|900) ;;
    *) TMOUT=900 ;;
esac
readonly TMOUT
export TMOUT
IHL_TIMEOUT
done
# login.defs is image-owned even when the upstream host platform excludes it.
if [ -f /etc/login.defs ]; then
    sed -i -E 's/^[[:space:]]*UMASK[[:space:]]+.*/UMASK 027/' /etc/login.defs
    grep -Eq '^UMASK[[:space:]]+027([[:space:]]|$)' /etc/login.defs
fi
# The service has no operating-system password login. Keep every password locked.
awk -F: ' $2 !~ /^[!*]/ {exit 1}' /etc/shadow
# Ubuntu retains PAM for vendor tools; restrict su to an empty dedicated group.
if [ -f /etc/pam.d/su ]; then
    if ! grep -q '^sugroup:' /etc/group; then
        ! grep -Eq '^[^:]+:[^:]*:65532:' /etc/group
        printf 'sugroup:x:65532:\n' >> /etc/group
    fi
    grep -Eq '^sugroup:[^:]*:[0-9]+:$' /etc/group
    printf '\nauth required pam_wheel.so use_uid group=sugroup\n' >> /etc/pam.d/su
fi
