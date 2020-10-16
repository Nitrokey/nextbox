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
#DAEMONIZE="-v `pwd`/../:/nextbox-dev"

SIGNED_MODEL=$(BINDDIR)/my.model
INSIDE_SIGNED_MODEL=$(DOCKER_SRCDIR)/my.model
drun=docker exec -it $(CONT_NAME)


create: $(MODEL_PATH) startup 
	cp -r $(MODEL_PATH) $(SIGNED_MODEL)
	$(drun) snap install snapcraft --classic
	$(drun) ubuntu-image snap $(INSIDE_SIGNED_MODEL)
	$(drun) mv /pi.img $(DOCKER_SRCDIR)/$(NAME).img
	mv $(BINDDIR)/$(NAME).img .


startup: clean
	
	mkdir -p $(BINDDIR)

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

image:
	docker build -t $(NAME)-builder --force-rm=true --rm=true $(DOCKERFILEDIR)

secrets:
	@echo "Missing: './secrets' directory"
	@false

$(MODEL_PATH):
	@echo "Missing: $(MODEL_PATH)"
	@echo "run 'make model' to create a model file"
	@false
