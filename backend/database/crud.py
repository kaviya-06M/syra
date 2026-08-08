from sqlalchemy.orm import Session
from . models import SystemMetric



#  WRITE — called by the agent scheduler every cycle


def save_metric(db: Session, cpu: float, memory: float, disk: float,
                network: float = 0.0, process_name: str = None) -> SystemMetric:
    """
    Insert one agent snapshot row into system_metrics.
    This data is later used by ML models for anomaly detection & failure prediction.
    """
    row = SystemMetric(
        cpu_usage=cpu,
        memory_usage=memory,
        disk_usage=disk,
        network_usage=network,
        process_name=process_name,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row



#  READ — used by ML pipeline to fetch training data


def get_all_metrics(db: Session, limit: int = 10000):
    """Return all stored snapshots for ML training."""
    return db.query(SystemMetric).order_by(SystemMetric.timestamp).limit(limit).all()


def get_recent_metrics(db: Session, limit: int = 100):
    """Return the most recent N snapshots for real-time inference."""
    return (
        db.query(SystemMetric)
        .order_by(SystemMetric.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_metric_count(db: Session) -> int:
    """Return total number of stored snapshots."""
    return db.query(SystemMetric).count()
