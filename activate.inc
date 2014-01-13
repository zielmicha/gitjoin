if [ ! -e virtualenv ]; then
    virtualenv virtualenv
    ./build_libgit.sh
fi

. virtualenv/bin/activate
export "CFLAGS=-I$PWD/virtualenv/local/include"
export "LDFLAGS=-L$PWD/virtualenv/local/lib"
export "LD_LIBRARY_PATH=$PWD/virtualenv/local/lib:$LD_LIBRARY_PATH"
export "DJANGO_SETTINGS_MODULE=webapp.settings"

pip install -qr requirements.txt
