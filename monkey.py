import sys
import os

# Remove any pre-imported modules
modules_to_remove = ['threading', 'socket', '_socket', 'select']
for module in modules_to_remove:
    if module in sys.modules:
        del sys.modules[module]

import eventlet

# Patch everything at once
eventlet.monkey_patch(
    all=True,
    aggressive=True
)

# Verify patching
import threading
import socket
import select

if not eventlet.patcher.is_monkey_patched(threading):
    print("Threading not properly patched!")
    sys.exit(1)