import psutil
from datetime import datetime


class NetworkCollector:

    def collect(self):

        net = psutil.net_io_counters()

        return {
            "timestamp": datetime.now().isoformat(),
            "bytes_sent": net.bytes_sent,
            "bytes_received": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_received": net.packets_recv
        }