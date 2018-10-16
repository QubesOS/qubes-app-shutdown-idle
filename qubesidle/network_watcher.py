#!/usr/bin/python3
# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
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

import asyncio
import pyudev
from . import idle_watcher


class NetworkWatcher(idle_watcher.IdleWatcher):
    def __init__(self):
        super().__init__()

        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by("net")

        self.devices = set()
        self.init_device_list()

        self.wait_future = None

    @asyncio.coroutine
    def wait_for_state_change(self):
        """
        Watching for events on udev network devices; if an event is adding or
        removing a network device whose name starts with 'vif', the method
        returns.

        :return: None
        """
        self.wait_future = asyncio.Future()
        self.monitor.start()
        asyncio.get_event_loop().add_reader(
            self.monitor.fileno(), self.device_event)

        try:
            yield from self.wait_future
        except asyncio.CancelledError:
            self.wait_future.cancel()

        asyncio.get_event_loop().remove_reader(self.monitor.fileno())

    def is_idle(self):
        """
        Check if current VM does not have any network interfaces named 'vif*'.

        :return: `True` if VM is idle, `False` otherwise
        """
        dev_list = self.context.list_devices().match_subsystem('net')
        for dev in dev_list:
            if dev.sys_name.startswith('vif'):
                return False
        return True

    def init_device_list(self):
        dev_list = self.context.list_devices().match_subsystem('net')
        for dev in dev_list:
            self.devices.add(dev.sys_name)

    def device_event(self):
        flag_for_end = False

        dev = self.monitor.poll()

        if not dev.sys_name.startswith('vif'):
            return

        if dev.action == 'add':
            self.devices.add(dev.sys_name)
            if len(self.devices) == 1:
                flag_for_end = True
        elif dev.action == 'remove':
            self.devices.remove(dev.sys_name)
            if not self.devices:
                flag_for_end = True

        if flag_for_end and self.wait_future:
            self.wait_future.set_result(True)
            self.wait_future = None
