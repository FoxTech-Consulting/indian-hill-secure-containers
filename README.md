# Indian Hill NGINX source

This immutable source snapshot contains the Secure and Hardened runtime recipes
for both supported NGINX version lines.

| Target | Recipe version | Public source tiers |
| --- | --- | --- |
| nginx | 1.30.6 | Secure, Hardened |
| nginx-mainline | 1.31.8 | Secure, Hardened |

List the recipes with Python 3. Build commands use Docker Buildx and linux/amd64:

```sh
python3 tools/build.py --list
python3 tools/build.py nginx --tier secure --dry-run
python3 tools/build.py nginx-mainline --tier hardened --dry-run
```

Remove --dry-run to build locally. Local images require their own assessment;
they do not inherit publication qualification. SOURCE.json binds every exported
file to the exact private family source revision. Historical published image
records retain their original source, signature and anonymous-download evidence
in published-images.json. See each record's exact source tag for its recipe.
