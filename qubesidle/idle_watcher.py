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

import abc
import asyncio


class IdleWatcher(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    async def wait_for_state_change(self):
        """
        Coroutine that watches for VM state changes. It must be an
        asyncio.coroutine and must return whenever VM idleness state changes
        (whether the change is from idle to busy or from busy to idle).
        Must handle asyncio.CancelledError gracefully - it means a timer ran out
        or another watcher reported a state change.

        :return: None
        """
        pass

    @abc.abstractmethod
    def is_idle(self):
        """
        Check if current VM is idle.

        :return: `True` if VM is idle, `False` otherwise
        """
        pass
