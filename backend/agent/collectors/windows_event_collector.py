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
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

            total = 0

            while total < 10:
                records = win32evtlog.ReadEventLog(hand, flags, 0)
                if not records:
                    break

                for event in records:
                    event_type = getattr(event, "EventType", 0)
                    is_error = event_type in (win32evtlog.EVENTLOG_ERROR_TYPE, win32evtlog.EVENTLOG_WARNING_TYPE)

                    if is_error:
                        events.append({
                            "event_id": event.EventID,
                            "source": event.SourceName,
                            "type": "Error" if event_type == win32evtlog.EVENTLOG_ERROR_TYPE else "Warning",
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