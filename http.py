# -*- coding: utf8 -*-

"""
考虑用http-parser代替
"""

import urlparse

# HTTP解析类型
HTTP_REQUEST_PARSER = 1
HTTP_RESPONSE_PARSER = 2


class ChunkParser(object):
    """
    HTTP chunked encoding response parser.
    """
    STATE_WAITING_FOR_SIZE = 1
    STATE_WAITING_FOR_DATA = 2
    STATE_COMPLETE = 3

    def __init__(self):
        self.state = ChunkParser.STATE_WAITING_FOR_SIZE
        self.body = b''
        self.chunk = b''
        self.size = None

    def parse(self, data):
        more = True if len(data) > 0 else False
        while more:
            more, data = self.process(data)

    def process(self, data):
        if self.state == ChunkParser.STATE_WAITING_FOR_SIZE:
            line, data = HttpParser.split(data)
            self.size = int(line, 16)
            self.state = ChunkParser.STATE_WAITING_FOR_DATA
        elif self.state == ChunkParser.STATE_WAITING_FOR_DATA:
            remaining = self.size - len(self.chunk)
            self.chunk += data[:remaining]
            data = data[remaining:]
            if len(self.chunk) == self.size:
                data = data[len(HttpParser.CRLF):]
                self.body += self.chunk
                if self.size == 0:
                    self.state = ChunkParser.STATE_COMPLETE
                else:
                    self.state = ChunkParser.STATE_WAITING_FOR_SIZE
                self.chunk = b''
                self.size = None
        return len(data) > 0, data


class HttpParser(object):
    """
    http协议解释器，解析HTTP请求和HTTP回包
    """
    # 状态机
    STATE_INITIALIZED = 1
    STATE_LINE_RCVD = 2
    STATE_RCVING_HEADERS = 3
    STATE_HEADERS_COMPLETE = 4
    STATE_RCVING_BODY = 5
    STATE_COMPLETE = 6
    # 分隔符
    CRLF, COLON, SPACE = b'\r\n', b':', b' '

    def __init__(self, h_type=None):
        self.type = h_type if h_type else HTTP_REQUEST_PARSER
        self.state = HttpParser.STATE_INITIALIZED
        # 通信原数据
        self.raw = b''
        # buffer为解析缓存
        self.buffer = b''

        self.method = None
        self.url = None
        self.headers = dict()
        self.body = None

        self.code = None
        self.reason = None
        self.version = None

        self.chunker = None
        self.host = None

    def input_data(self, data):
        """
        解析器入口
        :param data: 
        :return: 
        """
        self.raw += data
        data = self.buffer + data
        self.buffer = b''

        more = True if len(data) > 0 else False
        while more:
            more, data = self.process(data)
        self.buffer = data

    def process(self, data):
        """
        
        :param data: 
        :return: 
        """
        if self.state >= HttpParser.STATE_HEADERS_COMPLETE \
                and (self.method == b"POST"
                     or self.type == HTTP_RESPONSE_PARSER):
            if not self.body:
                self.body = b''

            if b'content-length' in self.headers:
                self.state = HttpParser.STATE_RCVING_BODY
                self.body += data
                if len(self.body) >= int(self.headers[b'content-length'][1]):
                    self.state = HttpParser.STATE_COMPLETE
            elif b'transfer-encoding' in self.headers \
                    and self.headers[b'transfer-encoding'][1].lower() == b'chunked':
                if not self.chunker:
                    self.chunker = ChunkParser()
                self.chunker.parse(data)
                if self.chunker.state == ChunkParser.STATE_COMPLETE:
                    self.body = self.chunker.body
                    self.state = HttpParser.STATE_COMPLETE

            return False, b''

        # 按HTTP协议，进行LINE或者HEADER分隔
        line, data = HttpParser.split(data)
        if line is False:
            return line, data

        if self.state < HttpParser.STATE_LINE_RCVD:
            self.process_line(line)
        elif self.state < HttpParser.STATE_HEADERS_COMPLETE:
            self.process_header(line)

        if self.state == HttpParser.STATE_HEADERS_COMPLETE \
                and self.type == HTTP_REQUEST_PARSER \
                and not self.method == b"POST" \
                and self.raw.endswith(HttpParser.CRLF*2):
            self.state = HttpParser.STATE_COMPLETE

        # 解析剩下的data，需要下次self.process处理
        return len(data) > 0, data

    def process_line(self, data):
        """
        行解析
        :param data: 
        :return: 
        """
        line = data.split(HttpParser.SPACE)

        if self.type == HTTP_REQUEST_PARSER:
            self.method = line[0].upper()
            self.url = urlparse.urlsplit(line[1])
            self.version = line[2]
        else:
            self.version = line[0]
            self.code = line[1]
            self.reason = b' '.join(line[2:])

        self.state = HttpParser.STATE_LINE_RCVD

    def process_header(self, data):
        """
        头解析
        :param data: 
        :return: 
        """
        if len(data) == 0:
            if self.state == HttpParser.STATE_RCVING_HEADERS:
                self.state = HttpParser.STATE_HEADERS_COMPLETE
            elif self.state == HttpParser.STATE_LINE_RCVD:
                self.state = HttpParser.STATE_RCVING_HEADERS
        else:
            self.state = HttpParser.STATE_RCVING_HEADERS
            parts = data.split(HttpParser.COLON)
            key = parts[0].strip()
            value = HttpParser.COLON.join(parts[1:]).strip()
            self.headers[key.lower()] = (key, value)
            if key == "Host":
                self.host = value

    def build_url(self):
        if not self.url:
            return b'/None'

        url = self.url.path
        if url == b'': url = b'/'
        if not self.url.query == b'': url += b'?' + self.url.query
        if not self.url.fragment == b'': url += b'#' + self.url.fragment
        return url

    def build_header(self, k, v):
        return k + b": " + v + HttpParser.CRLF

    def build(self, del_headers=None, add_headers=None):
        req = b" ".join([self.method, self.build_url(), self.version])
        req += HttpParser.CRLF

        if not del_headers: del_headers = []
        for k in self.headers:
            if not k in del_headers:
                req += self.build_header(self.headers[k][0], self.headers[k][1])

        if not add_headers: add_headers = []
        for k in add_headers:
            req += self.build_header(k[0], k[1])

        req += HttpParser.CRLF
        if self.body:
            req += self.body

        return req

    def is_headers_complete(self):
        return self.state >= HttpParser.STATE_HEADERS_COMPLETE

    def is_partial_body(self):
        return self.state == HttpParser.STATE_RCVING_HEADERS

    def is_message_complete(self):
        return self.state == HttpParser.STATE_COMPLETE

    @staticmethod
    def split(data):
        pos = data.find(HttpParser.CRLF)
        if pos == -1:
            return False, data
        line = data[:pos]
        data = data[pos+len(HttpParser.CRLF):]
        return line, data
