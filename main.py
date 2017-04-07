# -*- coding: utf8 -*-

import socket

from events import event_manager
from http import HttpParser
from store import store
import requests


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

        self.request = HttpParser()

    def run(self):
        event_manager.add(self.cli_sock, "r", self.read_handler)
        event_manager.add(self.cli_sock, "w", self.write_handler)

    def read_handler(self):
        data = self.cli_sock.recv(8192)
        if len(data) < 0:
            print("some error")
            self.remove_self()
            return
        if len(data) == 0:
            print("client close!")
            self.remove_self()
            return

        print data
        self.request.input_data(data)


        if self.request.is_message_complete():
            if "baidu" not in self.request.url.netloc:
                return 
            key = self.request.url.scheme + "://" + self.request.url.netloc + self.request.url.path
            value = store.get_content(key)
            if value == None:
                response = requests.get(key)
                print "%s" % response.text
                store.add(key, response.text)



    def write_handler(self):
        if not self.need_write:
            return

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
        event_manager.add_sock(a.cli_sock, a.read_handler, a.write_handler)


if __name__ == '__main__':
    pi = ProxyIn("127.0.0.1", 6777)
    pi.run()
