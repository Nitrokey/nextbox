
Steps to set up a development environment:

* you need to be able to run `docker`
* set up your NextBox, 
  * install your public key for ssh access
  * ssh on the NextBox and install the same public key for `root`
* checkout the `nextbox` repository
* inside `nextbox/debian` run `make dev-image` to create the docker image for development
* change into the container `make enter-dev-docker`
  * inside `/build/repos/app/nextbox/` run `npm install`
  * exit the docker
* modify the `DEV_DEVICE` variable inside `nextbox/debian/repos` to match your NextBox' local IP

Now the environment setup is done, for development you just run (inside `nextbox/debian/repos`):

* `make watch-update-app`
* `make watch-update-daemon`

in two different terminals. You can now modify the `app` and `daemon` contents (develop stuff)
and once you save a file the necessary builds are run and the results (if successfull) will be
copied onto the NextBox and all related tools/daemons will be restarted.

For testing make sure you disable any browser caching, e.g., Chromium: `F12` -> Network -> disable cache.

