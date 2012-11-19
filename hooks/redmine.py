import urllib
import sys

hostname, apikey, projectid = sys.argv[1:]

params = {'key': apikey, 'id': projectid}
if not projectid:
    del params['id']

url = 'http://%s/sys/fetch_changesets?%s' % (
    urllib.quote(hostname),
    urllib.urlencode(params)
)
print 'Notyfing Redmine at %r about changes...' % hostname,
sys.stdout.flush()
code = urllib.urlopen(url).getcode()
if code == 200:
    print 'done'
else:
    print 'finished with code', code
