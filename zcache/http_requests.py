# -*- coding: utf8 -*-
"""
requests包补丁
"""

import requests
import socket
from dns_query import get_a_record

from requests.packages.urllib3.connection import HTTPConnection
from requests.packages.urllib3.util import connection
from requests.packages.urllib3.exceptions import ConnectTimeoutError
from socket import timeout as SocketTimeout

def patched_new_conn(self):
    """ Establish a socket connection and set nodelay settings on it

    :return: a new socket connection
    """
    # resolve hostname to an ip address; use your own
    # resolver here, as otherwise the system resolver will be used.
    hostname = get_a_record(self.host)
    print "==========121=============:%s,type: %s, %s, :%d" % (hostname, type(hostname), self.host, self.port)

    extra_kw = {}
    if self.source_address:
        extra_kw['source_address'] = self.source_address

    if self.socket_options:
        extra_kw['socket_options'] = self.socket_options

    try:
        conn = connection.create_connection(
            (hostname, self.port), self.timeout, **extra_kw)

    except SocketTimeout:
        raise ConnectTimeoutError(
            self, "Connection to %s timed out. (connect timeout=%s)" %
                  (self.host, self.timeout))

    return conn

HTTPConnection._new_conn = patched_new_conn

if __name__ == '__main__':
    t = requests.get("http://www.baidu.com")
    print t.text