#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -e virtualenv ]; then
    virtualenv virtualenv
fi
. activate.inc
pip install -r requirements.txt

python manage.py "$@"
