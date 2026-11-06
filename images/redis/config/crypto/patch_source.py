"""Patch only the pinned Redis assessment binary; reject unexpected source."""
import argparse
import hashlib
import json
from pathlib import Path


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Redis cryptographic integration source anchor changed")
    return text.replace(before, after, 1)


def patch(root):
    originals = {name: (root / 'src' / name).read_bytes()
                 for name in ('acl.c', 'util.c', 'server.c')}
    acl = originals['acl.c'].decode()
    acl = replace_once(acl, '#include "sha256.h"', '#include "sha256.h"\n#include "ihl_crypto.h"')
    acl = replace_once(acl, '    SHA256_CTX ctx;\n    unsigned char hash[SHA256_BLOCK_SIZE];',
                       '    unsigned char hash[SHA256_BLOCK_SIZE];')
    acl = replace_once(acl, '    sha256_init(&ctx);\n    sha256_update(&ctx,(unsigned char*)cleartext,len);\n    sha256_final(&ctx,hash);',
                       '    ihlCryptoSha256(cleartext, len, hash);')
    util = originals['util.c'].decode()
    start = util.index('/* Get random bytes, attempts to get an initial seed')
    end = util.index('/* Generate the Redis "Run ID"', start)
    util = (util[:start] + '#include "ihl_crypto.h"\n'
            '/* All callers use the provider DRBG; failure has no weaker fallback. */\n'
            'void getRandomBytes(unsigned char *p, size_t len) {\n'
            '    ihlCryptoRandom(p, len);\n}\n\n' + util[end:])
    server = replace_once(originals['server.c'].decode(), '#include "server.h"',
                          '#include "server.h"\n#include "ihl_crypto.h"')
    server = replace_once(server, 'int main(int argc, char **argv) {',
                          'int main(int argc, char **argv) {\n'
                          '    ihlCryptoStartup();\n'
                          '    if (argc == 2 && strcmp(argv[1], "--ihl-crypto-check") == 0) {\n'
                          '        ihlCryptoValidate();\n'
                          '        puts("IHL Redis cryptographic checks passed");\n'
                          '        return 0;\n'
                          '    }\n')
    patched = {'acl.c': acl, 'util.c': util, 'server.c': server}
    # Check every anchor before writing any file.
    receipt = {'schemaVersion': 1, 'status': 'patched', 'qualificationStatus': 'pending', 'files': {}}
    for name, value in patched.items():
        data = value.encode()
        (root / 'src' / name).write_bytes(data)
        receipt['files'][name] = {'sourceSha256': hashlib.sha256(originals[name]).hexdigest(),
                                 'patchedSha256': hashlib.sha256(data).hexdigest()}
    (root / 'src' / 'ihl_crypto.h').write_bytes(Path(__file__).with_name('ihl_crypto.h').read_bytes())
    (root / 'ihl-crypto-patch.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    patch(parser.parse_args().source)
