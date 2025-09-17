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

TEST_TIMEOUT = 15
LOOP_TIMEOUT = 5
class IdleWatcherAlwaysIdle(idle_watcher.IdleWatcher):
    def __init__(self):
        super().__init__()

    async def wait_for_state_change(self):
        try:
            await asyncio.sleep(100000000000)
        except asyncio.CancelledError:
            return

    def is_idle(self):
        return True


class IdleWatcherIdleAfter3s(idle_watcher.IdleWatcher):
    def __init__(self):
        super().__init__()
        self.state = False

    async def wait_for_state_change(self):
        try:
            if not self.state:
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(1000000)
            self.state = True
            return
        except asyncio.CancelledError:
            return

    def is_idle(self):
        return self.state


class IdleWatcherIdleStateChange(idle_watcher.IdleWatcher):
    def __init__(self):
        super().__init__()

    async def wait_for_state_change(self):
        try:
            await asyncio.sleep(1)
            return
        except asyncio.CancelledError:
            return

    def is_idle(self):
        return False


class MonitorTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize event loop for Python 3.14 compatibility
        asyncio.set_event_loop(asyncio.new_event_loop())
        idleness_monitor.TIMEOUT_SECONDS = LOOP_TIMEOUT
        self.monitor = idleness_monitor.IdlenessMonitor()

    async def test_00_no_watcher(self):
        task  = asyncio.create_task(self.monitor.monitor_idleness())
        done, pending = await asyncio.wait([task], timeout=TEST_TIMEOUT)
        for p in pending:
            p.cancel()
        self.assertEqual(len(done), 0)

    async def test_01_always_idle(self):
        watcher = IdleWatcherAlwaysIdle()
        self.monitor.add_watcher(watcher)
        task  = asyncio.create_task(self.monitor.monitor_idleness())
        done, pending = await asyncio.wait([task], timeout=TEST_TIMEOUT)
        self.assertEqual(len(done), 1)

    async def test_02_idle_after_3s_2s(self):
        watcher = IdleWatcherIdleAfter3s()
        self.monitor.add_watcher(watcher)
        task  = asyncio.create_task(self.monitor.monitor_idleness())
        done, pending = await asyncio.wait([task], timeout=2)
        self.assertEqual(len(done), 0)

    async def test_03_idle_after_3s_10s(self):
        watcher = IdleWatcherIdleAfter3s()
        self.monitor.add_watcher(watcher)
        task  = asyncio.create_task(self.monitor.monitor_idleness())
        done, pending = await asyncio.wait([task], timeout=TEST_TIMEOUT)
        self.assertEqual(len(done), 1)

    async def test_04_idle_after_3s_two_watchers(self):
        watcher = IdleWatcherIdleAfter3s()
        watcher2 = IdleWatcherAlwaysIdle()

        self.monitor.add_watcher(watcher)
        self.monitor.add_watcher(watcher2)

        task  = asyncio.create_task(self.monitor.monitor_idleness())
        done, pending = await asyncio.wait([task], timeout=TEST_TIMEOUT)
        self.assertEqual(len(done), 1)

    async def test_05_never_idle_state_change(self):
        watcher = IdleWatcherIdleStateChange()

        self.monitor.add_watcher(watcher)

        task  = asyncio.create_task(self.monitor.monitor_idleness())
        done, pending = await asyncio.wait([task], timeout=TEST_TIMEOUT)
        self.assertEqual(len(done), 0)


if __name__ == "__main__":
    unittest.main()
