key=~/.ssh/id_rsa.pub

if [ -f $key ]; then
    encoded="`python -c "import urllib, sys; print urllib.quote(open(sys.argv[1]).read())" $key`"
    url="__URL__?key=$encoded"
    if [ -e "`which x-www-browser`" -a "$DISPLAY" != "" ]; then
        x-www-browser $url
    else
        echo "Open in your browser:"
        echo $url
    fi
else
    echo $key doesn\'t exist, aborting.
fi
