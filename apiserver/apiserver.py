#!/usr/bin/env python
import cgi
import datetime
import json
import logging
import optparse
import os.path
import random
import re
import sys
import time
import uuid
import xml.sax.saxutils

import boto.dynamodb
import boto.dynamodb.condition
import cherrypy
import ThreeScalePY

THREESCALE_PROVIDER_KEY = "5513eb02d039b694ae6946077eb5bdf2"

cherrypy.tools.parse_json = cherrypy.Tool('before_request_body',cherrypy.lib.jsontools.json_in)

class Website:
    def __init__(self):
        self.boto_connection = boto.dynamodb.connect_to_region("us-west-1")
        self.table = self.boto_connection.get_table("table")
    
    @cherrypy.expose
    @cherrypy.tools.parse_json()
    @cherrypy.tools.allow(methods=['GET','POST'])
    def default(self, custid, resource_name, key=None):
        if cherrypy.request.method == 'GET':
            return self.handle_get_for_customer(custid, key)
        else:
            return self.handle_post()
    
    def handle_get_for_customer(self, custid, key):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        ThreeScalePY.ThreeScaleAuthorizeUserKey(THREESCALE_PROVIDER_KEY, None, None, key).authorize()
        hash_key = custid
        #upper_timestamp = time.time()
        upper_timestamp = 1201934760.0 + 1800
        lower_timestamp = upper_timestamp - 3600
        range_key_condition = boto.dynamodb.condition.BETWEEN(lower_timestamp, upper_timestamp)
        entries = self.table.query(hash_key, range_key_condition)
        print repr(entries)
        result = {}
        result["custid"] = custid
        result["entries"] = []
        for entry in entries:
            result["entries"].append(entry)
        return json.dumps(result)
    
    def handle_post(self):
        json_object = cherrypy.request.json
        print repr(json_object)
        custid = json_object["custid"]
        key = json_object["key"]
        entries = json_object["entries"]
        
        ThreeScalePY.ThreeScaleAuthorizeUserKey(THREESCALE_PROVIDER_KEY, None, None, key).authorize()
        
        # {
        #     'custid': 'c00db300',
        #     'key': '84904069f5d7b6434a040fdebc3a8942',
        #     'entries': [
        #         {
        #             'status': '404',
        #             'bytes': '209',
        #             'request': 'GET /favicon.ico HTTP/1.1',
        #             'user-agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
        #             'identd': '-',
        #             'host': '208.64.240.130',
        #             'user': '-',
        #             'referrer': '-',
        #             'timestamp': 1201934760.0
        #             }
        #         ]
        #     }
        for entry in entries:
            timestamp = entry["timestamp"] + random.random()
            attrs = {
                "custid" : custid,
                "timestamp" : timestamp,
                "status" : entry["status"],
                "bytes" : entry["bytes"]
                }
            item = self.table.new_item(hash_key=custid, range_key=timestamp, attrs=attrs)
            item.put()
        return "OK"
    
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET','HEAD'])
    @cherrypy.tools.encode(encoding='UTF-8')
    def ping(self):
        return "OK"
    
    @cherrypy.expose
    @cherrypy.tools.encode(encoding='UTF-8')
    #@cherrypy.tools.parse_json()
    @cherrypy.tools.expires(secs=0)
    def diag(self):
        request_line = '"%s"' % cherrypy.request.request_line
        headers = "".join(["%s: %r\r\n" % (h,v) for (h,v) in cherrypy.request.header_list])
        body = cherrypy.request.body.read()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        #print repr(cherrypy.request.body.processors)
        return "= DIAG =\r\n" + request_line + "\r\n" + headers + "\r\n\r\n" + body

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    @cherrypy.tools.encode(encoding='UTF-8')
    @cherrypy.tools.expires(secs=0)
    def describetable(self):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return str(self.boto_connection.describe_table("table"))

def error_5xx_page(status, message, traceback, version):
    cherrypy.tools.expires.callable(secs=0)
    return "500 error"

def error_404_page(status, message, traceback, version):
    cherrypy.tools.expires.callable(secs=0)
    return "404 error"

def error_4xx_page(status, message, traceback, version):
    cherrypy.tools.expires.callable(secs=0)
    if status == "400 Bad Request":
        status = "Error"
    #template = templates.error4xx.error4xx()
    #template.status=status
    #template.message=message
    #return template.respond()
    return status

def main(argv):
    site_config = {
        'server.socket_host':'0.0.0.0',
        'server.socket_port':8080,
        'server.thread_pool':10,
        'server.socketQueueSize':10,
        'engine.autoreload_on':True
        # 'error_page.400':error_4xx_page,
        # 'error_page.401':error_4xx_page,
        # 'error_page.402':error_4xx_page,
        # 'error_page.403':error_4xx_page,
        # 'error_page.404':error_404_page,
        # 'error_page.405':error_4xx_page,
        # 'error_page.406':error_4xx_page,
        # 'error_page.407':error_4xx_page,
        # 'error_page.408':error_4xx_page,
        # 'error_page.409':error_4xx_page,
        # 'error_page.410':error_4xx_page,
        # 'error_page.411':error_4xx_page,
        # 'error_page.412':error_4xx_page,
        # 'error_page.413':error_4xx_page,
        # 'error_page.414':error_4xx_page,
        # 'error_page.415':error_4xx_page,
        # 'error_page.416':error_4xx_page,
        # 'error_page.417':error_4xx_page,
        # 'error_page.default':error_5xx_page
        }
    cherrypy.config.update(site_config)
    
    root = Website()
    
    # access log
    #fname = os.path.abspath(os.path.join(os.path.dirname(__file__), 'log', 'access'))
    #h = logging.handlers.TimedRotatingFileHandler(fname, 'H', 1, encoding='utf-8', utc=True)
    #h.setLevel(logging.DEBUG)
    #h.setFormatter(cherrypy._cplogging.logfmt)
    #cherrypy.log.access_log.addHandler(h)
    
    # error log
    #fname = os.path.abspath(os.path.join(os.path.dirname(__file__), 'log', 'error'))
    #h = logging.handlers.TimedRotatingFileHandler(fname, 'H', 1, encoding='utf-8', utc=True)
    #h.setLevel(logging.DEBUG)
    #h.setFormatter(cherrypy._cplogging.logfmt)
    #cherrypy.log.error_log.addHandler(h)
    #logging.getLogger().addHandler(h)
    #logging.getLogger().setLevel(logging.ERROR)
    
    # Turn off console log
    #cherrypy.log.screen = False
    
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    root.static = cherrypy.tools.staticdir.handler(section='/static', dir=static_dir)
    app_config = {'/':{}}
    cherrypy.quickstart(root, '/', app_config)
    return 0


if __name__ == '__main__':
    exit_status = main(sys.argv)
    sys.exit(int(exit_status))
