#!/bin/bash

vergt() {
	[[ `python3 -c "from packaging import version; print(version.parse('$1') > version.parse('$2'))"` == *"True"* ]] && [[ "$1" != "$2" ]]
	}

last_tag=$(git tag -l --sort=authordate | tail -n 1)
last_full_version=$(head -n 1 debian/changelog | grep -Eo '[0-9\.\-]*')
last_version=$(echo $last_full_version | cut -d "-" -f 1)

if [[ `git branch --show-current` != "master" ]]; then
	echo "[ERR] Other branch than master detected!"
	echo "[ERR] Exiting, please make sure to start this script only from master branch!"
	exit 1
fi

if vergt ${last_version} ${last_tag}; then
	echo "[i] adding tag 'v${last_version}'"
	git tag v${last_version}
	git push --tags
	echo "[i] tag 'v${last_version}' successfully added as successor of tag '${last_tag}'!"
else
	echo "[ERR] New version 'v${last_version}' incompatible: has to be newer than last tag '${last_tag}'!"
	exit 1
fi
