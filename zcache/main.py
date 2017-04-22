# -*- coding: utf8 -*-

import socket

from events import event_manager
from http import HttpParser
from store import store
import requests
from collections import OrderedDict
import json

# for HTTPConnection
import http_requests



IP1 = "104.199.248.104"
IP1 = "59.108.139.1"


class Connection(object):
    """
    网络连接
    """

    def __init__(self, sock):
        self.sock = sock

    def recv(self):
        data = self.sock.recv()
        return data

    def send(self, data):
        self.sock.send(data)


class ProxyOut(object):
    """
    代理出
    """


class ClientHandler(object):
    def __init__(self, cli_sock, cli_addr):
        self.cli_sock = cli_sock
        self.cli_addr = cli_addr
        self.need_write = False

        self.send_data = b""
        self.request = HttpParser()

    #def run(self):
    #    event_manager.add(self.cli_sock, "r", self.read_handler)
        #event_manager.add(self.cli_sock, "w", self.write_handler)

    def read_handler(self):
        try:
            data = self.cli_sock.recv(81920)
        except socket.error as msg:
            print msg
            self.remove_self()
            return

        if len(data) < 0:
            print("some error")
            self.remove_self()
            return
        if len(data) == 0:
            print("client close!")
            self.remove_self()
            return

        #print data
        self.request.input_data(data)
        #print data

        if self.request.is_message_complete():
            print self.request.url.netloc

            print "====================:" + self.request.host

            key1 = "http://" + self.request.host + self.request.url.geturl()

            print "try: %s, from: %s" % (key1, self.cli_addr)

            headers = OrderedDict()
            for k in self.request.headers:
                tp = self.request.headers[k]
                headers[tp[0]] = tp[1]

            cc = json.dumps(headers)
            print cc
            response = requests.get(key1, headers=headers, stream=True)

            content = response.raw.read()
            print "url: %s" % (key1)

            print response.headers
            if "Content-Encoding" in response.headers:
                if response.headers["Content-Encoding"] == "gzip":

                    print "len vs: %s, %s" % (response.headers["Content-Length"], str(len(content)))
                    response.headers["Content-Length"] = str(len(content))

            cc = "%s %s %s" % (self.request.version, response.status_code, response.reason)
            cc += b"\r\n"
            for i in response.headers:
                if i == "Transfer-Encoding":
                    continue
                cc += i
                cc += ": "
                cc += response.headers[i]
                cc += b"\r\n"
            cc += b"\r\n"


            pp_len = 0
            #buff = ""
            #for chunk in response.iter_content(chunk_size=1024):
            #    if chunk:
            #        buff += chunk
            #        pp_len += len(chunk)
            cc += content
            self.send_data += cc
            self.need_write = True
            event_manager.add(self.cli_sock, "w", self.write_handler)
            #while True:
            #    tmp = response.raw.read(100)
            #    if not tmp:
            #        break
            #    cc += tmp
            #    tt1 += len(tmp)
            #    print "cccc: :%d" % tt1
            #print cc
            #with open("test.html", "wb") as f:
            #    f.write(cc)
            #len1 = self.cli_sock.send(cc)
            #print "send: %s, rawsize: %d, size: %d" % (key1, len(cc), len1)

            # self.cli_sock.close()
            #value = store.get_content(key)
            #if value == None:
            #    response = requests.get(key)
            #    print "%s" % response.text
            #    store.add(key, response.text)

            #    requests.Response()
            #    if not response.raw:
            #        print type(response.raw)
            #        print response.raw


            #self.cli_sock.send(re)
        else:
            print '>>>>>>>>>>>>>'

    def write_handler(self):
        #print 'write.....'
        if len(self.send_data) > 0:

            send_size = min(2048, len(self.send_data))
            tmp = self.send_data[0:send_size]
            self.send_data = self.send_data[send_size:]
            if len(tmp) > 0:
                self.cli_sock.send(tmp)
            if len(self.send_data) == 0:
                self.need_write = False
                event_manager.remove(self.cli_sock, "w")

    def remove_self(self):
        if self.cli_sock:
            self.cli_sock.close()

        event_manager.remove_sock(self.cli_sock)


class ProxyIn(object):
    """
    代理进
    """
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.backlog = 5
        self.socket = None

    def __del__(self):
        if self.socket:
            self.socket.close()

    def run(self):
        """
        主函数，死循环接受客户端的请求申请
        :return: 
        """
        # 启动事件循环进程
        # self.start_event_process()

        # 初始化监听
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(self.backlog)

        event_manager.add(self.socket, "r", self.accept_handler)

        event_manager.run()

    def accept_handler(self):
        conn, addr = self.socket.accept()
        a = ClientHandler(conn, addr)
        print addr
        #conn.setblocking(0)
        event_manager.add_sock(a.cli_sock, a.read_handler, a.write_handler)


if __name__ == '__main__':
    pi = ProxyIn("127.0.0.1", 80)
    pi.run()
