#!/bin/bash 

source shared_vars.txt

if [[ "$1" == "" ]]; then
	echo "usage: $0 <secrets-dir>"
	echo
	echo "referenced <secrets-dir> shall contain:"
	echo "- snapcraft-credentials.txt (to login to snapcraft)"
	echo "- dot_snap                  (root-user's .snap dir containing signing key)"
	echo
	exit 1
fi

# outside container (on host)
secretsdir=$1
workdir=$(pwd)/workdir.model
echo "shared workdir: $workdir"

# inside the container
inside_workdir=/nextbox
inside_secretsdir=${inside_workdir}/secrets
inside_creds=${inside_secretsdir}/${SNAP_LOGIN_FILE}

inside_exec="docker exec -it ${CONT_NAME}"

# prepare container workdir and start it up
rm -rf ${workdir}
mkdir -p ${workdir}
cp -r ${secretsdir} ${workdir}/secrets 

make startup BINDDIR=${workdir} 

${inside_exec} snap install snapcraft --classic

${inside_exec} rm -rf /root/.snap
${inside_exec} cp -r ${inside_secretsdir}/dot_snap /root/.snap

# start working inside the container  
${inside_exec} snapcraft login --with ${inside_creds}

# create base .json model
developer_id=$(${inside_exec} snapcraft whoami | tail -n1 | cut -d " " -f 2 | xargs)
snaps='["nextcloud-nextbox"]'
timestamp=$(date -Iseconds --utc)

model_json_tmpl=model.json.tmpl
model_json_path=${workdir}/model.json
inside_model_json_path=${inside_workdir}/model.json

sed -e "s@%%snaps%%@${snaps}@g" \
	  -e "s@%%developer_id%%@${developer_id}@g" \
		-e "s@%%timestamp%%@${timestamp}@g" ${model_json_tmpl} \
		| sed -e 's/\r//g' \
		> ${model_json_path}

# running once for passsword
${inside_exec} snap sign -k ${KEY_NAME} ${inside_model_json_path}

# running a 2nd time, no need for pass, thus output can be redirected
new_model_path=${MODEL_PATH}.$(date +%s)
${inside_exec} snap sign -k ${KEY_NAME} ${inside_model_json_path} > ${new_model_path}

echo
echo "json model assertion:              ${model_json_path}"
echo "signed model assertion:            ${new_model_path}"
echo "secrets in workdir (delete them!): ${workdir}/secrets"


