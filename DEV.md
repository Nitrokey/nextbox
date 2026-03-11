
Steps to set up a development environment:

* you need to be able to run `docker`
* set up your NextBox, 
  * install your public key for ssh access
  * ssh on the NextBox and install the same public key for `root`
* checkout the `nextbox` repository
* inside `nextbox/debian` run `make dev-image` to create the docker image for development
* modify the `DEV_DEVICE` variable inside `nextbox/debian/repos` to match your NextBox' local IP

Update the app or the daemon on the NextBox:

* `make update-app`
* `make update-daemon`

For a permanent "watching" behavior, you run (inside `nextbox/debian/repos`):

* `make watch-update-app`
* `make watch-update-daemon`

in two different terminals. You can now modify the `app` and `daemon` contents (develop stuff)
and once you save a file the necessary builds are run and the results (if successfull) will be
copied onto the NextBox and all related tools/daemons will be restarted.

For testing make sure you disable any browser caching, e.g., Chromium: `F12` -> Network -> disable cache.

