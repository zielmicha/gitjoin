if [ ! -e virtualenv ]; then
    virtualenv virtualenv
    ./build_libgit.sh
fi

. activate_base.inc

pip install -qr requirements.txt
