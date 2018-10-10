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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import abc
import asyncio


class IdleWatcher(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def wait_for_state_change(self):
        pass

    @abc.abstractmethod
    def is_idle(self):
        pass


class IdleWatcherTestTrue(IdleWatcher):
    def __init__(self):
        super().__init__()

    @asyncio.coroutine
    def wait_for_state_change(self):
        try:
            yield from asyncio.sleep(10)
            return
        except asyncio.CancelledError:
            return

    def is_idle(self):
        return True


class IdleWatcherTestFalse(IdleWatcher):
    def __init__(self):
        super().__init__()

    @asyncio.coroutine
    def wait_for_state_change(self):
        try:
            yield from asyncio.sleep(10)
        except asyncio.CancelledError:
            return

    def is_idle(self):
        return True
