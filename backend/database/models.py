from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
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


class Incident(Base):
    """A diagnosis snapshot retained for feedback and root-cause ML training."""

    __tablename__ = "incidents"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_data = Column(Text, nullable=False)
    anomaly_info = Column(Text, nullable=False, default="{}")
    matched_rules = Column(Text, nullable=False, default="[]")
    evidence = Column(Text, nullable=False, default="[]")
    rule_root_cause = Column(String, nullable=True)
    rule_confidence = Column(Float, nullable=False, default=0.0)
    ml_root_cause = Column(String, nullable=True)
    ml_confidence = Column(Float, nullable=True)
    final_root_cause = Column(String, nullable=True)
    final_confidence = Column(Float, nullable=False, default=0.0)
    remediation_action = Column(String, nullable=True)
    verification_resolved = Column(Boolean, nullable=True)


class IncidentFeedback(Base):
    """Human-verified label and outcome for one recorded incident."""

    __tablename__ = "incident_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String, nullable=False, unique=True, index=True)
    feedback = Column(String, nullable=False)  # confirmed | corrected | unknown
    verified_root_cause = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    remediation_verified = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
