#!/bin/bash


pushd "$1" >/dev/null
python3 -m http.server -b 127.0.0.1 &
popd >/dev/null
echo $! >server.pid
