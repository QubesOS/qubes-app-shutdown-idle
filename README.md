Qubes Shutdown Idle Script
---------------------

This is a simple script that watches the current qube for idleness and, if it's 
idle for more than 15 minutes (timeout time is defined in
 `qubesidle.idleness_monitor`), shuts it down.

At the moment, only checking for visible windows is supported - when a VM has no
visible windows for more than 15 minutes, it's going to be shut down. The 
mechanism is opt-in - enable `shutdown-idle` service in qube settings to use it.

If needed, other watching methods can be added: check the qubesidle Python 
module for details (in brief: all you need is a Python module supporting a
couple methods).
