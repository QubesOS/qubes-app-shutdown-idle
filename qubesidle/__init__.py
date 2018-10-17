"""
To add additional watchers, create a Python package containing a class
that implements idle_watcher.IdleWatcher interface and an entry_point in this
package called qubes_idle_watcher that points to that class.

The class should implement two methods: asyncio coroutine wait_for_state_change
and a normal method is_idle that returns a bool. For more details, see class
idle_watcher.IdleWatcher.
"""