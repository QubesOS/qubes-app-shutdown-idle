#!/usr/bin/python3
# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2015 Marek Marczykowski-Górecki
#                              <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#


import xcffib as xcb
from xcffib import xproto

import select
import time


class IdleWatcher(object):
    def __init__(self):
        self.idle_timeout = 5*60

        self.conn = xcb.connect()
        self.setup = self.conn.get_setup()
        self.root = self.setup.roots[0].root

        self.windows = set()

    def watch_window(self, w):
        self.conn.core.ChangeWindowAttributesChecked(
            w, xproto.CW.EventMask, [xproto.EventMask.PropertyChange])

    def initial_sync(self):
        cookie = self.conn.core.QueryTree(self.root)
        root_tree = cookie.reply()
        cookies = {}
        for w in root_tree.children:
            cookies[w] = self.conn.core.GetWindowAttributes(w)
            print("initial: {!s}".format(w))
        for w, cookie in cookies.items():
            attr = cookie.reply()
            if attr.map_state == xproto.MapState.Viewable:
                self.windows.add(w)
                print("initial viewable: {!s}".format(w))

    def watch_for_idle(self):
        self.conn.core.ChangeWindowAttributesChecked(
            self.root, xproto.CW.EventMask,
            [xproto.EventMask.SubstructureNotify])
        self.conn.flush()
        self.initial_sync()
        x_fd = self.conn.get_file_descriptor()
        idle_start = None

        while True:
            if idle_start:
                remaining_timeout = time.time() - idle_start + self.idle_timeout
            else:
                remaining_timeout = None
            fd_r, fd_w, fd_e = select.select([x_fd], [], [], remaining_timeout)
            if fd_r:
                for ev in iter(self.conn.poll_for_event, None):
                    if isinstance(ev, xproto.CreateNotifyEvent):
                        print("create: {!s}, count: {!s}".format(ev.window, len(self.windows)))
                    elif isinstance(ev, xproto.MapNotifyEvent):
                        self.windows.add(ev.window)
                        print("map: {!s}, count: {!s}".format(ev.window, len(self.windows)))
                        idle_start = None
                    elif isinstance(ev, xproto.UnmapNotifyEvent):
                        self.windows.discard(ev.window)
                        print("unmap: {!s}, count: {!s}".format(ev.window, len(self.windows)))
                        if not self.windows:
                            print("empty!")
                            idle_start = time.time()
                    elif isinstance(ev, xproto.DestroyNotifyEvent):
                        print("destroy: {!s}, count: {!s}".format(ev.window, len(self.windows)))
            if idle_start and idle_start + self.idle_timeout < time.time():
                print("idle!!!!!")


if __name__ == '__main__':
    retriever = IdleWatcher()
    retriever.watch_for_idle()

