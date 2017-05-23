#!/bin/bash


pushd "$1" >/dev/null
python3 -m http.server &
popd >/dev/null
echo $! >server.pid
