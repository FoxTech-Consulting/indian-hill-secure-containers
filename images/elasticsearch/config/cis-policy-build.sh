#!/bin/sh
# Only this disposable stage installs the real policy generator.
set -eu
. /etc/os-release
mkdir -p /ihl-cis-policy-files/usr/share/ihl
if [ "$ID" = ubuntu ] && [ "$VERSION_ID" = 24.04 ]; then
    printf 'Ubuntu 24.04: RHEL crypto-policy generator not applicable.\n' > /ihl-cis-policy-files/usr/share/ihl/cis-crypto-policy-build.txt
    exit 0
fi
[ "$ID" = rhel ]
case "$VERSION_ID" in 9|9.*) ;; *) exit 1 ;; esac
version=$(rpm -q --qf '%{VERSION}-%{RELEASE}' crypto-policies)
test -n "$version"
microdnf install --setopt=tsflags=nodocs -y "crypto-policies-scripts-$version"
[ "$(rpm -q --qf '%{VERSION}-%{RELEASE}' crypto-policies)" = "$version" ]
[ "$(rpm -q --qf '%{VERSION}-%{RELEASE}' crypto-policies-scripts)" = "$version" ]
modules=/etc/crypto-policies/policies/modules
mkdir -p "$modules"
printf 'cipher@SSH = -*-CBC\n' > "$modules/NO-SSHCBC.pmod"
printf 'cipher@SSH = -3DES-CBC -AES-128-CBC -AES-192-CBC -AES-256-CBC -CHACHA20-POLY1305\n' > "$modules/NO-SSHWEAKCIPHERS.pmod"
printf 'mac@SSH = -HMAC-MD5* -UMAC-64* -UMAC-128*\n' > "$modules/NO-SSHWEAKMACS.pmod"
printf 'mac = -*-128*\n' > "$modules/NO-WEAKMAC.pmod"
policy=DEFAULT:NO-SHA1:NO-SSHCBC:NO-SSHWEAKCIPHERS:NO-SSHWEAKMACS:NO-WEAKMAC
if [ -f /etc/crypto-policies/back-ends/rpm-sequoia.config ]; then
    printf 'hash@rpm = -SHA1\n' > "$modules/NO-RPMSHA1.pmod"
    policy="$policy:NO-RPMSHA1"
fi
update-crypto-policies --set "$policy"
[ "$(update-crypto-policies --show)" = "$policy" ]
test -s /etc/crypto-policies/state/CURRENT.pol
# Dereference generated backend links so every effective file is in the final layer.
destination=/ihl-cis-policy-files/etc/crypto-policies
mkdir -p "$destination"
for item in back-ends state policies config; do
    cp -RL "/etc/crypto-policies/$item" "$destination/$item"
done
printf 'crypto-policies=%s\ncrypto-policies-scripts=%s\npolicy=%s\nqualificationGranted=false\n' "$version" "$version" "$policy" > /ihl-cis-policy-files/usr/share/ihl/cis-crypto-policy-build.txt
