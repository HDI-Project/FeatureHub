#!/usr/bin/env python

import binascii
import os

PATTERN = 'XYZ'

with open('./.env.local.example', 'r') as f:
    c = f.read()

while PATTERN in c:
    c = c.replace(PATTERN, binascii.b2a_hex(os.urandom(16)).decode("utf-8"), 1)

print(c)
