from datetime import datetime


class EventGenerator:

    def generate(
            self,
            cpu,
            memory,
            disk,
            network,
            process,
            events
    ):

        return {

            "timestamp": datetime.now().isoformat(),

            "cpu": cpu,

            "memory": memory,

            "disk": disk,

            "network": network,

            "processes": process,

            "windows_events": events

        }