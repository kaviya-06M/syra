try:
    import win32evtlog
except ImportError:
    win32evtlog = None


class WindowsEventCollector:

    def collect(self):
        if not win32evtlog:
            return []

        server = "localhost"
        logtype = "System"
        hand = None
        events = []

        try:
            hand = win32evtlog.OpenEventLog(server, logtype)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | \
                    win32evtlog.EVENTLOG_SEQUENTIAL_READ

            total = 0

            while total < 10:
                records = win32evtlog.ReadEventLog(hand, flags, 0)
                if not records:
                    break

                for event in records:
                    events.append({
                        "event_id": event.EventID,
                        "source": event.SourceName,
                        "time": str(event.TimeGenerated)
                    })
                    total += 1
                    if total >= 10:
                        break
        except Exception as e:
            print(f"[WindowsEventCollector] Warning: {e}")
        finally:
            if hand:
                try:
                    win32evtlog.CloseEventLog(hand)
                except Exception:
                    pass

        return events