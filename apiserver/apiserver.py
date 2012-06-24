#!/usr/bin/env python
import cgi
import datetime
import logging
import optparse
import os.path
import re
import sys
import time
import uuid
import xml.sax.saxutils

import cherrypy

class Website:
    def __init__(self):
        pass
    
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET','HEAD'])
    @cherrypy.tools.encode(encoding='UTF-8')
    def ping(self):
        return "Health check passed."
    
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    @cherrypy.tools.encode(encoding='UTF-8')
    @cherrypy.tools.expires(secs=0)
    def diag(self):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return "= Request Headers =\r\n" + "".join(["%s: %r\r\n" % (h,v) for (h,v) in cherrypy.request.header_list])

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
        'engine.autoreload_on':True,
        'error_page.400':error_4xx_page,
        'error_page.401':error_4xx_page,
        'error_page.402':error_4xx_page,
        'error_page.403':error_4xx_page,
        'error_page.404':error_404_page,
        'error_page.405':error_4xx_page,
        'error_page.406':error_4xx_page,
        'error_page.407':error_4xx_page,
        'error_page.408':error_4xx_page,
        'error_page.409':error_4xx_page,
        'error_page.410':error_4xx_page,
        'error_page.411':error_4xx_page,
        'error_page.412':error_4xx_page,
        'error_page.413':error_4xx_page,
        'error_page.414':error_4xx_page,
        'error_page.415':error_4xx_page,
        'error_page.416':error_4xx_page,
        'error_page.417':error_4xx_page,
        'error_page.default':error_5xx_page
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
