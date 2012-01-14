#!/usr/bin/env bash

ping -o $1
say "$1 is ready for login"
sleep 1
ssh $@
