import time
import psutil
from datetime import datetime


class NetworkCollector:

    def __init__(self):
        self.last_time = None
        self.last_sent = None
        self.last_recv = None

    def collect(self):
        net = psutil.net_io_counters()
        now = time.time()

        bytes_sent_rate = 0.0
        bytes_recv_rate = 0.0

        if self.last_time is not None and now > self.last_time:
            dt = now - self.last_time
            if dt > 0:
                bytes_sent_rate = max(0.0, (net.bytes_sent - (self.last_sent or net.bytes_sent)) / dt)
                bytes_recv_rate = max(0.0, (net.bytes_recv - (self.last_recv or net.bytes_recv)) / dt)

        self.last_time = now
        self.last_sent = net.bytes_sent
        self.last_recv = net.bytes_recv

        return {
            "timestamp": datetime.now().isoformat(),
            "bytes_sent": net.bytes_sent,
            "bytes_received": net.bytes_recv,
            "bytes_sent_per_sec": round(bytes_sent_rate, 2),
            "bytes_recv_per_sec": round(bytes_recv_rate, 2),
            "packets_sent": net.packets_sent,
            "packets_received": net.packets_recv
        }