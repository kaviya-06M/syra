from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
# SYSTEM METRIC SCHEMAS

class SystemMetricCreate(BaseModel):
    """
    Data coming from monitoring agent
    """

    cpu_usage: float
    memory_usage: float
    disk_usage: float

    network_usage: Optional[float] = 0.0

    process_name: Optional[str] = None



class SystemMetricResponse(BaseModel):

    id: int

    cpu_usage: float
    memory_usage: float
    disk_usage: float

    network_usage: float

    process_name: Optional[str]

    timestamp: datetime


    class Config:
        from_attributes = True

# ANOMALY DETECTION SCHEMAS


class AnomalyCreate(BaseModel):

    anomaly_type: str

    anomaly_score: float

    severity: str


class AnomalyResponse(BaseModel):

    id: int

    anomaly_type: str

    anomaly_score: float

    severity: str

    timestamp: datetime


    class Config:
        from_attributes = True

# ROOT CAUSE ANALYSIS SCHEMAS



class RootCauseResult(BaseModel):

    problem: str

    root_cause: str

    confidence: float

    evidence: List[str]



class Recommendation(BaseModel):

    action: str

    explanation: str

    requires_permission: bool



class DiagnosisResponse(BaseModel):

    incident_id: str

    status: str


    anomaly_type: str

    severity: str


    root_cause: RootCauseResult


    recommendations: List[Recommendation]




# LLM RESPONSE SCHEMA


class SYRAResponse(BaseModel):

    message: str

    diagnosis: Optional[DiagnosisResponse] = None

    voice_enabled: bool = False

# CHAT SCHEMAS



class ChatRequest(BaseModel):

    user_message: str



class ChatResponse(BaseModel):

    syra_message: str

    timestamp: datetime

# REMEDIATION SCHEMAS


class RemediationRequest(BaseModel):

    action: str

    user_permission: bool



class RemediationResponse(BaseModel):

    action: str

    status: str

    result: str