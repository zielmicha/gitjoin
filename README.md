# gitjoin

## Installation

Install requirements:

    # For example on Debian/Ubuntu:
    apt-get install build-essential git python2.7-dev python-virtualenv cmake

Generate and edit configuration file.

    ./genconf.sh > config.py
    nano config.py

`./update` will install dependencies, build libgit2 and create DB tables:

    ./update

If anything fails (for example you forgot to install dependencies), `rm virtualenv`
and try again.

Create first user:

    ./manage.sh createsuperuser

Run test server

    ./manage.sh runserver 7000

You can visit administrator interface at http://localhost:7000/global/admin/

For deployment, uwsgi is recommended:

    source activate.inc
    pip install uwsgi
    hash -r
    uwsgi --deamonize=var/git.log uwsgi.ini

And use your favourite reverse-proxy to forward requests to http://localhost:8080

### Enabling SSH Git transport

    mv ~/.ssh/authorized_keys ~/authorized_keys.custom
    source activate.inc
    python -m gitjoin.authorized_keys

### Using built-in SSH server

Gitjoin may also run separate SSH server on port 2022 if you prefer not exposing OpenSSH:

    source activate.inc
    pip install -r requirements_sshd.txt
    python -m gitjoin.sshd

### Using PostgreSQL instead of SQlite

If you want to host a site with a bit bigger traffic edit `config.py` to point to
your PostgreSQL database and install PostgreSQL adapter:

    source activate.inc
    pip install psycopg2
