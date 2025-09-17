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

import os
import asyncio
import subprocess
import importlib.metadata

TIMEOUT_SECONDS = 15 * 60


class IdlenessMonitor(object):
    def __init__(self):
        self.watchers = []
        self.watch_the_watchers = None

    def load_watchers(self):
        """
        Load IdleWatchers as defined by entry points named idle_watcher.

        :return: None
        """
        for entry_point in importlib.metadata.entry_points(
                group='qubes_idle_watcher'):
            self.add_watcher(entry_point.load()())

    def add_watcher(self, watcher):
        """
        Add an IdleWatcher; must be called at least once for the monitor to
        actually do something.

        :param watcher: an object implementing idle_watcher.IdleWatcher class
        :return: None
        """
        self.watchers.append(watcher)
        if self.watch_the_watchers:
            self.watch_the_watchers.set_result(True)
            self.watch_the_watchers = None

    async def monitor_idleness(self):
        """
        Main idleness detection routine. It watches for any state changes
        detected by watchers (supplied via add_watcher), and if a change is
        detected, the monitor checks if all watchers report idleness.
        If no, watching for state changes resumes.
        If yes, watching resumes with a timeout given by TIMEOUT_SECONDS; if
        timeout is exceeded without any state change events, the function
        returns.

        :return: None
        """
        count_idleness = 0

        while True:
            if not self.watchers:
                self.watch_the_watchers = asyncio.Future()
                await self.watch_the_watchers
            tasks = []
            for w in self.watchers:
                tasks.append(asyncio.create_task(w.wait_for_state_change()))

            # Wait is with a timeout, to avoid possible watcher bugs
            wait_for_change_with_timeout = asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=TIMEOUT_SECONDS)

            # noinspection PyTupleAssignmentBalance
            done, pending = await wait_for_change_with_timeout

            for task in pending:
                task.cancel()
                await task

            all_idle = all(w.is_idle() for w in self.watchers)

            if all_idle:
                count_idleness += 1
            else:
                count_idleness = 0

            if count_idleness > 1:
                return


def main():
    """
    Main function.
    :return: None
    """

    # check if the correct service ('shutdown-idle') was enabled
    if not os.path.exists('/var/run/qubes-service/shutdown-idle'):
        return

    # Initialize event loop for Python 3.14 compatibility
    asyncio.set_event_loop(asyncio.new_event_loop())

    monitor = IdlenessMonitor()
    monitor.load_watchers()

    asyncio.run(monitor.monitor_idleness())

    subprocess.call(['sudo', 'poweroff'])


if __name__ == '__main__':
    main()
