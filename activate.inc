if [ ! -e virtualenv ]; then
    virtualenv virtualenv
    ./build_libgit.sh
fi

source activate_base.inc

pip install -qr requirements.txt
