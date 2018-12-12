#!/usr/bin/env bash

if ping -o $1; then
    say "$1 is ready for login" &
    ssh $@
fi
