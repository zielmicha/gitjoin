hostname=`hostname -f`
domain=`hostname -d`
echo URL = \'http://$hostname/\'
echo USERNAME = \'`whoami`\'
echo HOSTNAME = \'$hostname\'
echo
echo AUTHENTICATION_BACKENDS = \(
echo "    'gitjoin.auth_backend.CASBackend',"
echo "    # or 'webapp.auth_backend.PAMBackend'"
echo \)
echo CAS_SERVER_URL = \'http://webauth.$domain/\'


secretkey=$(python -c 'import os; print os.urandom(30).encode("base64")')
echo SECRET_KEY = \'$secretkey\'

cat config.py.example
echo
