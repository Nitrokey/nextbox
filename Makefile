include shared_vars.txt

NAME=nextbox
BASEDIR=$(shell pwd)

WORKDIR=workdir.image
BINDDIR=$(BASEDIR)/$(WORKDIR)
DOCKER_SRCDIR=/$(NAME)

DOCKERFILEDIR=$(BASEDIR)/

# disabled for now
#DOCKERUIDGID=$(shell id -u):$(shell id -g)
#DOCKERUSER=$(DOCKERUIDGID)
DOCKERUSER=root:root

#DAEMONIZE=
DAEMONIZE=-d

SIGNED_MODEL=$(BINDDIR)/my.model
INSIDE_SIGNED_MODEL=$(DOCKER_SRCDIR)/my.model
drun=docker exec $(CONT_NAME)


# start not as dep, or we need some hack to show make it's running...
create: $(MODEL_PATH) startup 
	cp -r $(MODEL_PATH) $(SIGNED_MODEL)
	$(drun) snap install snapcraft --classic
	$(drun) ubuntu-image snap $(INSIDE_SIGNED_MODEL)

startup: clean
	
	mkdir -p $(WORKDIR)

	docker run -ti \
		--user $(DOCKERUSER) \
		--name $(CONT_NAME) \
		--mount type=bind,source=$(BINDDIR),target=$(DOCKER_SRCDIR) \
		--cap-add SYS_ADMIN \
    --device=/dev/fuse \
    --security-opt apparmor:unconfined \
    --security-opt seccomp:unconfined \
    -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
    -v /lib/modules:/lib/modules:ro \
		$(DAEMONIZE) $(NAME)-builder

	# wait a little as this container really "boots" ...
	sleep 10

clean:
	@-docker stop $(CONT_NAME)
	@-docker rm $(CONT_NAME)
	rm -rf ${WORKDIR}

model: secrets
	bash create_model.sh secrets

	echo "---"
	echo "--- to use the model, copy it manually to $(MODEL_PATH) ---"
	echo "---"

image:
	docker build -t $(NAME)-builder --force-rm=true --rm=true $(DOCKERFILEDIR)

secrets:
	echo "Missing: './secrets' directory"

$(MODEL_PATH):
	echo "Missing: $(MODEL_PATH)"
	echo "run 'make model' to create a model file"
