#!/bin/bash

vergt() {
	[[ `python3 -c "from packaging import version; print(version.parse('$1') > version.parse('$2'))"` == *"True"* ]]
	}


last_full_version=$(head -n 1 debian/changelog | grep -Eo '[0-9\.\-]*')
last_version=$(echo $last_full_version | cut -d "-" -f 1)
last_release=$(echo $last_full_version | cut -d "-" -f 2)

version=$1
release=$2
tmp_path=/tmp/changelog.tmp.debian.nextbox.txt
branch_name=v${version}-${release}-pr

echo
echo "[i] CURRENT VERSION:  ${last_full_version}" 
echo



if [[ "$1" == "" || "$2" == "" || "$3" != "" ]]; then
	echo "[ERR] missing argument(s)... "
	echo "[i] usage: ./$0 <version> <release>"
	exit 1
fi

if [[ `git branch --show-current` != "master" ]]; then
	echo "[ERR] Other branch than master detected!"
	echo "[ERR] Exiting, please make sure to start this script only from master branch!"
	exit 1
fi

if vergt ${last_version} ${version}; then
	echo [ERR] \"$version\" is not 'newer' compared to: \"$last_version\"
	echo [ERR] Exiting, please pass valid version
	exit 1
fi

if `git branch -a | grep ${branch_name}`; then
	echo "[ERR] ${version}-${release} has been released already!"
	echo "[ERR] Exiting, please use a new version number"
	exit 1
fi

cleanup() {
	git checkout master
	git branch -D ${branch_name}
}



echo "[i] LAST RELEASE: ${last_version}-${last_release}"
echo "[i] THIS RELEASE: ${version}-${release}"
echo
echo

echo "[?] Should I continue preparing the release? (ctrl+c to cancel)"
echo
echo "[!] Continuing here will start changing your git repository!"
echo
echo "[!] Did you change the 'appinfo/info.xml' version, if the nextcloud app was updated????"
echo "[!] Did you change the 'package.json' version, if the nextcloud app was updated????"
read

# check nc update

compose=daemon/nextbox-compose/docker-compose.yml
pushd .. > /dev/null
git checkout -b ${branch_name}

if [[ `git status -s | wc -l` == 1 ]] && git status -s | grep ${compose}; then
	nc_ver=$(grep -m 1 "image: nextcloud" ${compose} | cut -d : -f 3 | cut -d - -f 1)

	echo "[i] NextCloud update to version ${nc_ver} detected"
	echo
	echo "[?] Should i continue committing the NextCloud update? (ctrl+c to cancel)"
	echo "[!] If you cancel here you have to cleanup git manually (git branch -D ${branch_name})!"
	read


	echo "Committing update to NC ${nc_ver}"
	git add ${compose}
	git commit -m "update to NC ${nc_ver}"

elif ! git diff-index --quiet HEAD --; then
  echo "[ERR] repository has changes - aborting..."
	popd > /dev/null
	cleanup
	exit 1
else
	echo "[+] repository clean"
fi

popd > /dev/null


# author_name=$(git config --get author.name)
# author_email=$(git config --get user.email)
changes=$(git log v${last_version}..HEAD --oneline | cut -d " " -f 2- | sed 's/^/  * /')

cat > ${tmp_path} <<EOL
%%PKG%% (${version}-${release}) focal; urgency=low

  ${changes}

 -- Markus Meissner (Debian) <coder@safemailbox.de>  $(date -R)

EOL


# -- ${author_name} (Debian) <${author_email}>  $(date -R)


#pushd repos/daemon > /dev/null
# git tag v${version}
# git push --tags
# echo "[i] added tag 'v${version}' for daemon repo"
#popd > /dev/null

#pushd repos/app > /dev/null
#git tag v${version}
#git push ssh --tags
#echo "[i] added tag 'v${version}' for app repo"
#popd > /dev/null

########
######## sed -E 's/^.*version.*$/        "version": "4.3.5",/g' package.json
########

echo [!] Please review the changelog and make any changes if necessary.
echo [!] Note that all changes are written to the changelog: be careful!
echo [i] Removing all content from the changelog aborts this process!
read


cat debian/changelog >> ${tmp_path}
$EDITOR ${tmp_path}

if [[ -z "$(cat ${tmp_path})" ]]; then
	echo [!] Aborting: empty changelog
	cleanup
	exit 1
fi

cp ${tmp_path} debian/changelog

echo [i] Commiting to new branch ${branch_name}

git add debian/changelog
git commit -m "changelog v${version}"

echo [i] Pushing to origin/v${version}-pr
git push --quiet -u origin ${branch_name}
git checkout master

echo [!] Create a Pull Request here: https://github.com/Nitrokey/nextbox/pull/new/${branch_name}
echo [!] Once this is merged create a tag using tag_release.sh


#cat ${tmp_path}
