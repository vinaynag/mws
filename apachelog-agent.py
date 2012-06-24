import apachelog
import sys
import json

import time, datetime
def date_conv(ts1):
    t1 = time.strptime(ts1.strip('[]').split()[0], '%d/%b/%Y:%H:%M:%S')
    d1 = datetime.datetime(*t1[:6])
    return d1

# Format copied and pasted from Apache conf - use raw string + single quotes
format = r'%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'

import cookielib
import socket
import urllib
import urllib2

url = 'http://api.serverlytics.com/c00db300/entries/'
http_header = {
                "Content-type": "application/json",
                }


# setup socket connection timeout
timeout = 15
socket.setdefaulttimeout(timeout)

# setup cookie handler
cookie_jar = cookielib.LWPCookieJar()
cookie = urllib2.HTTPCookieProcessor(cookie_jar)

# setup proxy handler, in case some-day you need to use a proxy server
proxy = {} # example: {"http" : "www.blah.com:8080"}

# create an urllib2 opener()
#opener = urllib2.build_opener(proxy, cookie) # with proxy
opener = urllib2.build_opener(cookie) # we are not going to use proxy now

# create your HTTP request
#req = urllib2.Request(url, urllib.urlencode(params), http_header)

# submit your request
#res = opener.open(req)
#html = res.read()

# save retrieved HTML to file
#open("tmp.html", "w").write(html)
#print html

def post_entries(entries):
    json_object = {
        "custid":"c00db300",
        "key":"84904069f5d7b6434a040fdebc3a8942",
        "entries":entries
        }
    body = json.dumps(json_object)
    print body
    # create your HTTP request
    req = urllib2.Request(url, body, http_header)
    res = opener.open(req)

#p = apachelog.parser(format)
p = apachelog.parser(apachelog.formats['extended'])
filename = sys.argv[1]
entries = []
for line in open(filename):
	data = p.parse(line)
	#print data
        entry = {}
        #print data["%h"]
	entry["host"]=data["%h"]
	entry['identd']= data["%l"]
        entry['user']= data["%u"]
	mm = date_conv(data["%t"])
        entry['timestamp']= time.mktime(mm.timetuple()) 
        entry['request']= data["%r"]
        entry['status']= data["%>s"]
        entry['bytes']= data["%bytes"]
        entry['referrer']= data["%{Referer}i"]
        entry['user-agent']= data["%{User-agent}i"]
	entries.append(entry)
	if(len(entries) > 10):
            post_entries(entries)
            entries = []

if(entries):
    post_entries(entries)
