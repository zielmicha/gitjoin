# gitjoin

## Installation

    ./genconf.py > config.py
    # adjust config
    nano config.py
    # install requirements, create DBs, etc
    ./update
    # create first user
    ./manage.sh createsuperuser
    # run test server
    ./manage.sh runserver 7000

Visit administrator interface at http://localhost:7000/global/admin/
