import urllib
import sys

url = sys.argv[1]
show_url = sys.argv[2] == 'false'
if not url.startswith(('http://', 'https://')):
    sys.exit(('Invalid URL: %r' % (url if show_url else '[hidden]')))

print 'Fetching', (repr(url) if show_url else 'hook url') + '...',
sys.stdout.flush()
urllib.urlopen(url).read(1024)
print 'done'
