# gitjoin

## Installation

Install requirements:

    # For example on Debian/Ubuntu:
    apt-get install build-essential git python2.7-dev python-virtualenv

Generate and edit configuration file.

    ./genconf.sh > config.py
    nano config.py
    
`./update` will install dependencies, build libgit2 and create DB tables:

    ./update
    
Create first user:

    ./manage.sh createsuperuser
    
Run test server

    ./manage.sh runserver 7000

You can visit administrator interface at [http://localhost:7000/global/admin/]

For deployment, uwsgi is recommended:
    
    . activate.sh
    pip install uwsgi
    hash -r 
    uwsgi uwsgi.ini
    
And use your favourite reverse-proxy to forward requests to http://localhost:8080
