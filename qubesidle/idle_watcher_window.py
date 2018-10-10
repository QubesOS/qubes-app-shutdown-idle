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

# must implement idle_watcher.IdleWatcher
# methods: wait_for_state_change (@asyncio.coroutine), takes no arguments,
# returns when state change is detected, must handle asyncio.CancelledError
# is_idle, not a coroutine, returns whether is idle (True) or not (False)


import xcffib
from xcffib import xproto
import asyncio
from . import idle_watcher


class IdleWatcher(idle_watcher.IdleWatcher):
    def __init__(self):
        super(IdleWatcher, self).__init__()

        self.conn = xcffib.connect()
        self.setup = self.conn.get_setup()
        self.root = self.setup.roots[0].root

        atom = self.conn.core.InternAtom(
            False, len("_NET_SUPPORTING_WM_CHECK"),
            "_NET_SUPPORTING_WM_CHECK").reply().atom
        self.qubes_window_id = self.conn.core.GetProperty(
            False,  # delete
            self.root,  # window
            atom,
            xproto.Atom.WINDOW,
            0,  # long_offset
            512 * 1024 # long_length
        ).reply().value.to_atoms()[0]
        # the thing above is equivalent to writing
        #  xprop -root _NET_SUPPORTING_WM_CHECK

        self.windows = set()

        self.wait_future = None

        file_descriptor = self.conn.get_file_descriptor()
        loop = asyncio.get_event_loop()
        loop.add_reader(file_descriptor, self.read_events)

        self.initial_sync()

    def initial_sync(self):
        cookie = self.conn.core.QueryTree(self.root)
        root_tree = cookie.reply()
        cookies = {}
        for w in root_tree.children:
            if w == self.qubes_window_id:
                continue
            cookies[w] = self.conn.core.GetWindowAttributes(w)
        for w, cookie in cookies.items():
            attr = cookie.reply()
            if attr.map_state == xproto.MapState.Viewable:
                self.windows.add(w)

    @asyncio.coroutine
    def wait_for_state_change(self):

        self.conn.core.ChangeWindowAttributesChecked(
            self.root, xproto.CW.EventMask,
            [xproto.EventMask.SubstructureNotify])
        self.conn.flush()

        self.wait_future = asyncio.Future()

        try:
            yield from self.wait_future
        except asyncio.CancelledError:
            self.wait_future.cancel()
        return

    def read_events(self):
        flag_for_end = False
        for ev in iter(self.conn.poll_for_event, None):
            if ev.window == self.qubes_window_id:
                continue
            if isinstance(ev, xproto.MapNotifyEvent):
                if not self.windows:
                    flag_for_end = True
                self.windows.add(ev.window)
            elif isinstance(ev, xproto.UnmapNotifyEvent):
                self.windows.discard(ev.window)
                if not self.windows:
                    flag_for_end = True

        if flag_for_end:
                self.wait_future.set_result(True)

    def is_idle(self):
        cookie = self.conn.core.QueryTree(self.root)
        root_tree = cookie.reply()
        for w in root_tree.children:
            try:
                if w == self.qubes_window_id:
                    continue
                attr = self.conn.core.GetWindowAttributes(w).reply()
                if attr.map_state == xproto.MapState.Viewable:
                    return False
            except xcffib.xproto.WindowError:
                continue
        return True
