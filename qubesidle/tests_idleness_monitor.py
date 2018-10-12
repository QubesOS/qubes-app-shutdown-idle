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

import unittest
import asyncio
from . import idleness_monitor
from . import idle_watcher


class IdleWatcherAlwaysIdle(idle_watcher.IdleWatcher):
    def __init__(self):
        super().__init__()

    @asyncio.coroutine
    def wait_for_state_change(self):
        try:
            yield from asyncio.sleep(100000000000)
        except asyncio.CancelledError:
            return

    def is_idle(self):
        return True


class IdleWatcherIdleAfter10s(idle_watcher.IdleWatcher):
    def __init__(self):
        super().__init__()
        self.state = False

    @asyncio.coroutine
    def wait_for_state_change(self):
        self.state = False
        try:
            yield from asyncio.sleep(10)
            self.state = True
            return
        except asyncio.CancelledError:
            self.state = False
            return

    def is_idle(self):
        return self.state


class IdleWatcherIdleStateChange(idle_watcher.IdleWatcher):
    def __init__(self):
        super().__init__()
        self.state = False

    @asyncio.coroutine
    def wait_for_state_change(self):
        self.state = False
        try:
            yield from asyncio.sleep(1)
            return
        except asyncio.CancelledError:
            return

    def is_idle(self):
        return False


class MonitorTest(unittest.TestCase):
    def setUp(self):
        self.monitor = idleness_monitor.IdlenessMonitor()
        self.loop = asyncio.get_event_loop()

    def test_00_no_watcher(self):
        task = asyncio.wait([self.monitor.monitor_idleness()], timeout=5)
        done, pending = self.loop.run_until_complete(task)
        for p in pending:
            p.cancel()
        self.assertEqual(len(done), 0)

    def test_01_always_idle(self):
        watcher = IdleWatcherAlwaysIdle()
        self.monitor.add_watcher(watcher)
        task = asyncio.wait([self.monitor.monitor_idleness()], timeout=5)
        done, pending = self.loop.run_until_complete(task)
        self.assertEqual(len(done), 0)

    def test_02_idle_after_10s_5s(self):
        watcher = IdleWatcherIdleAfter10s()
        self.monitor.add_watcher(watcher)
        task = asyncio.wait([self.monitor.monitor_idleness()], timeout=5)
        done, pending = self.loop.run_until_complete(task)
        self.assertEqual(len(done), 0)

    def test_03_idle_after_10s_15s(self):
        watcher = IdleWatcherIdleAfter10s()
        self.monitor.add_watcher(watcher)
        task = asyncio.wait([self.monitor.monitor_idleness()], timeout=15)
        done, pending = self.loop.run_until_complete(task)
        self.assertEqual(len(done), 1)

    def test_04_idle_after_10s_two_watchers(self):
        watcher = IdleWatcherIdleAfter10s()
        watcher2 = IdleWatcherAlwaysIdle()

        self.monitor.add_watcher(watcher)
        self.monitor.add_watcher(watcher2)

        task = asyncio.wait([self.monitor.monitor_idleness()], timeout=15)
        done, pending = self.loop.run_until_complete(task)
        self.assertEqual(len(done), 1)

    def test_05_never_idle_state_change(self):
        watcher = IdleWatcherIdleStateChange()

        self.monitor.add_watcher(watcher)

        task = asyncio.wait([self.monitor.monitor_idleness()], timeout=15)

        done, pending = self.loop.run_until_complete(task)
        self.assertEqual(len(done), 0)


if __name__ == "__main__":
    unittest.main()
