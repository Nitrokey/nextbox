#!/bin/bash


if [[ "$1" == "" || "$2" == "" || "$3" != "" ]]; then
	echo "usage: $0 <version> <release>"
	exit 1
fi

version=$1
release=$2
tmp_path=/tmp/changelog.tmp.debian.nextbox.txt

last_full_version=$(head -n 1 debian/changelog | grep -Eo '[0-9\.\-]*')
last_version=$(echo $last_full_version | cut -d "-" -f 1)
last_release=$(echo $last_full_version | cut -d "-" -f 2)

pushd repos/daemon > /dev/null
if ! git diff-index --quiet HEAD --; then
    echo "[ERR] daemon repository has changes - aborting..."
		popd
		exit 1
else
		echo "[+] daemon repository clean"
		daemon_changes=$(git log v${last_version}..HEAD --oneline | cut -d " " -f 2-)
fi
popd > /dev/null

pushd repos/app > /dev/null
if ! git diff-index --quiet HEAD --; then
    echo "[ERR] app repository has changes - aborting..."
		popd
		exit 1
else
		echo "[+] app repository clean"
		app_changes=$(git log v${last_version}..HEAD --oneline | cut -d " " -f 2-)
fi
popd > /dev/null

echo "---"
echo $daemon_changes
echo $app_changes
echo "---"



if [[ `vercmp ${last_version} ${version}` != "-1" ]]; then
	echo ERROR: \"$version\" is not 'newer' compared to: \"$last_version\"
	echo ERROR: exiting, please pass valid version
	exit 1
fi


echo "[i] LAST RELEASE: ${last_version}-${last_release}"
echo "[i] THIS RELEASE: ${version}-${release}"


cat > ${tmp_path} <<EOL
%%PKG%% (${version}-${release}) groovy; urgency=low

  * app: ${app_changes}
	* daemon: ${daemon_changes}

 -- Markus Meissner (Debian) <coder@safemailbox.de>  $(date -R)

EOL

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
