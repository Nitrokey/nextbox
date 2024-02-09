#!/bin/bash

systemctl stop nextbox-compose.service
systemctl stop docker

rm -rf /srv/docker/*

reboot
