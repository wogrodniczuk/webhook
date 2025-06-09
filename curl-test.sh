#!/bin/bash

curl -k -X POST https://agent13417.azyl.ag3nts.org/webhook \
     -H "Content-Type: application/json" \
     -d '{"instruction": "poleciałem jedno pole w prawo"}'
