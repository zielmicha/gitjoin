#!/bin/bash
set -e
cd "$(dirname "$0")"
. activate.inc

python manage.py "$@"
