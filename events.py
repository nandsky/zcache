# -*- coding: utf8 -*-

import select


class Event(object):
    """
    描述一个事件，唯一索引为文件描述符
    """
    def __init__(self, who, event, do_what):
        self.obj = who
        self.event = event
        self.handler = do_what
        self.flag_remove = False


class EventManager(object):
    def __init__(self):
        self.rlist = []
        self.wlist = []
        self.xlist = []

        self.r_handlers = dict()
        self.w_handlers = dict()
        self.x_handlers = dict()

        # 添加handler需要枷锁
        self.locker = None

    def run(self):
        a = 1
        while True:
            a += 1
            r, w, x = select.select(self.rlist, [], self.xlist, 5)
            print "-----------------: %d" % a
            # read handler
            for r_item in r:
                self._do_handler(r_item, "r")
            # write handler
            for w_item in w:
                # read handler 和 write handler在共用一个socket时，会有冲突
                if not w_item:
                    self._do_handler(w_item, "w")
            # exception handler
            for x_item in x:
                if not x_item:
                    self._do_handler(x_item, "x")

            # 清理资源

    def _do_handler(self, who, event):
        """
        事件dispatcher
        :param who: 
        :param event: 
        :return: 
        """
        handlers = None
        if event == "r":
            handlers = self.r_handlers
        if event == "w":
            handlers = self.w_handlers
        if event == "x":
            handlers = self.x_handlers
        if not handlers:
            return

        if not handlers[who]:
            return
        handlers[who]()

    def add(self, who, event, do_what):
        """
        注册事件
        :param who: 
        :param event: 
        :param do_what: 
        :return: 
        """
        if event == "r":
            self.rlist.append(who)
            self.r_handlers[who] = do_what
        elif event == "w":
            self.wlist.append(who)
            self.w_handlers[who] = do_what
        elif event == "x":
            self.xlist.append(who)
            self.x_handlers[who] = do_what

    def add_sock(self, sock, do_in, do_out):
        self.add(sock, "r", do_in)
        self.add(sock, "w", do_out)

    def remove_sock(self, sock):
        if sock in self.rlist:
            self.rlist.remove(sock)
        if sock in self.wlist:
            self.wlist.remove(sock)

        if sock in self.xlist:
            self.xlist.remove(sock)

        self.r_handlers.pop(sock, None)
        self.w_handlers.pop(sock, None)
        self.x_handlers.pop(sock, None)


event_manager = EventManager()