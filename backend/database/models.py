from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime

from .database import Base


class SystemMetric(Base):
    """
    Stores every agent snapshot — used exclusively for ML training & prediction.
    Fields match the agent collectors output and schema.py exactly.
    """

    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # CPU
    cpu_usage = Column(Float, nullable=False)

    # Memory
    memory_usage = Column(Float, nullable=False)

    # Disk
    disk_usage = Column(Float, nullable=False)

    # Network (bytes sent per cycle — optional)
    network_usage = Column(Float, nullable=True, default=0.0)

    # Top process name by memory at time of snapshot
    process_name = Column(String, nullable=True)

    # Auto-stamped when row is inserted
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)