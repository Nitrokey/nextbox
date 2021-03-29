#!/bin/bash


if [[ "$1" == "" || "$2" == "" || "$3" != "" ]]; then
	echo "usage: $0 <version> <release>"
	exit 1
fi

version=$1
release=$2
tmp_path=/tmp/changelog.tmp.debian.nextbox.txt



pushd repos/daemon > /dev/null
if ! git diff-index --quiet HEAD --; then
    echo "[ERR] daemon repository has changes - aborting..."
		popd
		exit 1
else
		echo "[+] daemon repository clean"
fi
popd > /dev/null

pushd repos/app > /dev/null
if ! git diff-index --quiet HEAD --; then
    echo "[ERR] app repository has changes - aborting..."
		popd
		exit 1
else
		echo "[+] app repository clean"
fi
popd > /dev/null

echo "[i] LAST RELEASE: $(head -n 1 debian/changelog | grep -Eo '[0-9\.\-]*')"
echo "[i] THIS RELEASE: ${version}-${release}"


cat > ${tmp_path} <<EOL
%%PKG%% (${version}-${release}) groovy; urgency=low

  * %%CHANGELOG_1%%

 -- Markus Meissner (Debian) <coder@safemailbox.de>  $(date -R)

EOL

echo "TODO: git log ${last_version}..HEAD --oneline >> changelog"

echo "[?] Should I continue and add the version tags? (ctrl+c to cancel)"
read

pushd repos/daemon > /dev/null
git tag v${version}
git push ssh --tags
echo "[i] added tag 'v${version}' for daemon repo"
popd > /dev/null

pushd repos/app > /dev/null
git tag v${version}
git push ssh --tags
echo "[i] added tag 'v${version}' for app repo"
popd > /dev/null


cat debian/changelog >> ${tmp_path}
cp ${tmp_path} debian/changelog
vim debian/changelog


#cat ${tmp_path}
