#!/usr/bin/python3
# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2015 Marek Marczykowski-Górecki
#                               <marmarek@invisiblethingslab.com>
# Copyright (C) 2018 Marta Marczykowska-Górecka
#                               <marmarta@invisiblethingslab.com>
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.

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

        #  The lovecraftian nightmare below is equivalent to
        #  xprop -root _NET_SUPPORTING_WM_CHECK
        #  unfortunately, xcffib is low-level enough for this to be necessary.
        atom = self.conn.core.InternAtom(
            False, len("_NET_SUPPORTING_WM_CHECK"),
            "_NET_SUPPORTING_WM_CHECK").reply().atom
        self.qubes_window_id = self.conn.core.GetProperty(
            False,  # delete
            self.root,  # window
            atom,
            xproto.Atom.WINDOW,
            0,  # long_offset
            512 * 1024  # long_length
        ).reply().value.to_atoms()[0]

        self.windows = set()

        # an asyncio.Future used to communicate between wait_for_state_
        # change and read_events
        self.wait_future = None

        file_descriptor = self.conn.get_file_descriptor()
        loop = asyncio.get_event_loop()
        loop.add_reader(file_descriptor, self.read_events)

        self.conn.core.ChangeWindowAttributesChecked(
            self.root, xproto.CW.EventMask,
            [xproto.EventMask.SubstructureNotify])
        self.conn.flush()

        self.initial_sync()

    def initial_sync(self):
        """
        Iterate over all windows and add visible windows (that are not the qubes
        helper window) to the self.windows set.

        :return: None
        """
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

    async def wait_for_state_change(self):
        """
        Waits for changes in mapped/unmapped windows reported by X Window System
        via xcffib socket.
        Only a change from no windows to some windows, or from some windows to
        no windows, is reported.

        :return: None
        """
        self.wait_future = asyncio.Future()

        try:
            await self.wait_future
        except asyncio.CancelledError:
            self.wait_future.cancel()
        return

    def read_events(self):
        """
        Reports a change in mapped/unmapped X windows via setting
        self.wait_future to done. To avoid unnecessary traffic, this function
        reports only when the last window is unampped or, conversely, a window
        is mapped when no windows were mapped before.

        :return: None
        """
        flag_for_end = False
        for ev in iter(self.conn.poll_for_event, None):
            if ev.window == self.qubes_window_id:
                continue
            if isinstance(ev, xproto.MapNotifyEvent):
                if not self.windows:
                    flag_for_end = True
                self.windows.add(ev.window)
            elif isinstance(ev, xproto.UnmapNotifyEvent) and \
                    ev.window in self.windows:
                self.windows.discard(ev.window)
                if not self.windows:
                    flag_for_end = True

        if flag_for_end:
                self.wait_future.set_result(True)

    def is_idle(self):
        """
        Check whether any windows (other than Qubes helper window) are visible.

        :return: `True` when there are no windows visible and `False` otherwise
        """
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
                #  when windows are opened in quick succession, on rare
                #  occassions a window can vanish before we manage to iterate
                #  over it.
                continue
        return True
