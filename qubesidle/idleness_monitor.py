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

from . import idle_watcher  # this will be fixed one day
import asyncio
import subprocess

TIMEOUT_SECONDS = 1


class IdlenessMonitor(object):

    def __init__(self):
        self.watchers = []

    def add_watcher(self, watcher):
        self.watchers.append(watcher)

    @asyncio.coroutine
    def monitor_idleness(self):
        while True:
            if not self.watchers:
                yield from asyncio.sleep(1)
                continue
            tasks = []
            for w in self.watchers:
                tasks.append(w.wait_for_state_change())

            wait_for_change = asyncio.wait(tasks,
                                           return_when=asyncio.FIRST_COMPLETED)

            # noinspection PyTupleAssignmentBalance
            done, pending = yield from wait_for_change

            for task in pending:
                task.cancel()

            # watchers must handle CancelledError - add that to docu

            all_idle = all(w.is_idle() for w in self.watchers)

            if all_idle:
                tasks = []

                for w in self.watchers:
                    tasks.append(w.wait_for_state_change())

                wait_for_change_with_timeout = asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=TIMEOUT_SECONDS)

                # noinspection PyTupleAssignmentBalance
                done, pending = \
                    yield from wait_for_change_with_timeout
                if not done:
                    prep_for_shutdown = True
                else:
                    prep_for_shutdown = False

                for t in pending:
                    t.cancel()
                if prep_for_shutdown:
                    return


def main():
    monitor = IdlenessMonitor()

    # watchers = []
    # # here there be loading all watcher with some magic
    test_watcher = idle_watcher.IdleWatcherTestTrue()
    test_watcher2 = idle_watcher.IdleWatcherTestFalse()
    #
    monitor.add_watcher(test_watcher)
    monitor.add_watcher(test_watcher2)

    asyncio.get_event_loop().run_until_complete(monitor.monitor_idleness())

    print("SHUTDOWN")
    # subprocess.call(['sudo', 'poweroff'])  # is this good?


if __name__ == '__main__':
    main()
