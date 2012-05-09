hostname=`hostname -f`
domain=`hostname -d`
echo URL = \'http://$hostname/\'
echo USERNAME = \'`whoami`\'
echo HOSTNAME = \'$hostname\'
echo
echo AUTHENTICATION_BACKENDS = \(
echo "    'gitjoin.auth_backend.CASBackend',"
echo "    # or 'gitjoin.auth_backend.PAMBackend'"
echo \)
echo CAS_SERVER_URL = \'http://webauth.$domain/\'
git_core_path=`git --exec-path`
echo GIT_CORE_PATH = \'$git_core_path\'

secretkey=$(python -c 'import os; print os.urandom(30).encode("base64")')
echo SECRET_KEY = \'$secretkey\'

cat config.py.example
echo
