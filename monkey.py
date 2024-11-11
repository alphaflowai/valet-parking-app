import eventlet
eventlet.monkey_patch(
    os=True,
    select=True,
    socket=True,
    thread=True,
    time=True
)

# Force threading patch
import threading
assert eventlet.patcher.is_monkey_patched(threading)