"""
SYRA End-to-End Data Flow Verification
=======================================
Traces the EXACT pipeline the user described:

  Collectors --> EventGenerator --> Database --> DataCleaner
  --> FeatureEngineer --> FeatureScaler --> SequenceBuilder
  --> LSTM Autoencoder --> Reconstruction Error --> Threshold
  --> Anomaly Detector --> Failure Predictor --> Inference Engine
"""
import sys
import os
import json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def log(stage, status, detail=""):
    tag = PASS if status else FAIL
    msg = f"  {tag} {stage}"
    if detail:
        msg += f"  ->  {detail}"
    print(msg)
    results.append((stage, status, detail))


# ============================================================================
# STAGE 1: Agent Collectors
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 1: Agent Collectors (psutil -> raw dicts)")
print("=" * 70)

from backend.agent.collectors.cpu_collector import CPUCollector
from backend.agent.collectors.memory_collector import MemoryCollector
from backend.agent.collectors.disk_collector import DiskCollector
from backend.agent.collectors.network_collector import NetworkCollector
from backend.agent.collectors.process_collector import ProcessCollector
from backend.agent.collectors.windows_event_collector import WindowsEventCollector

cpu_data = CPUCollector().collect()
memory_data = MemoryCollector().collect()
disk_data = DiskCollector().collect()
network_data = NetworkCollector().collect()
process_data = ProcessCollector().collect()
windows_data = WindowsEventCollector().collect()

log("CPU Collector", "cpu_percent" in cpu_data, f"cpu_percent={cpu_data['cpu_percent']}")
log("Memory Collector", "memory_percent" in memory_data, f"memory_percent={memory_data['memory_percent']}")
log("Disk Collector", "disk_percent" in disk_data, f"disk_percent={disk_data['disk_percent']}")
log("Network Collector", "bytes_sent" in network_data, f"bytes_sent={network_data['bytes_sent']}")
log("Process Collector", "top_processes" in process_data, f"count={len(process_data.get('top_processes', []))}")
log("Windows Events", isinstance(windows_data, list), f"count={len(windows_data)}")


# ============================================================================
# STAGE 2: EventGenerator
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 2: EventGenerator (6 dicts -> unified JSON snapshot)")
print("=" * 70)

from backend.agent.event_generator import EventGenerator
generator = EventGenerator()
event = generator.generate(cpu_data, memory_data, disk_data, network_data, process_data, windows_data)

expected_keys = {"timestamp", "cpu", "memory", "disk", "network", "processes", "windows_events"}
log("EventGenerator", expected_keys.issubset(set(event.keys())), f"keys={list(event.keys())}")


# ============================================================================
# STAGE 3: Database Persistence
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 3: Database (save_metric -> SQLite)")
print("=" * 70)

from backend.database.database import SessionLocal
from backend.database.crud import save_metric, get_metric_count
from backend.database.migrations import run_migrations

run_migrations()
db = SessionLocal()
try:
    top_proc = process_data["top_processes"][0]["name"] if process_data.get("top_processes") else None
    row = save_metric(db, cpu=cpu_data["cpu_percent"], memory=memory_data["memory_percent"],
                      disk=disk_data["disk_percent"], network=network_data["bytes_sent"],
                      process_name=top_proc)
    total = get_metric_count(db)
    log("save_metric", row.id is not None, f"row_id={row.id}, total={total}")
finally:
    db.close()


# ============================================================================
# STAGE 4: DataCleaner
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 4: DataCleaner (raw event -> sanitized event)")
print("=" * 70)

from backend.preprocessing.cleaner import DataCleaner
cleaner = DataCleaner()
cleaned = cleaner.clean(event)

log("DataCleaner", "cpu" in cleaned, f"cpu={cleaned['cpu']['cpu_percent']}, mem={cleaned['memory']['memory_percent']}")

# Verify clamping
bad = cleaner.clean({"cpu": {"cpu_percent": 150}, "memory": {"memory_percent": -5}})
log("Clamping check", bad["cpu"]["cpu_percent"] == 100 and bad["memory"]["memory_percent"] == 0,
    f"150->{bad['cpu']['cpu_percent']}, -5->{bad['memory']['memory_percent']}")


# ============================================================================
# STAGE 5: FeatureEngineer
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 5: FeatureEngineer (cleaned event -> 11-dim float vector)")
print("=" * 70)

from backend.preprocessing.feature_engineering import FeatureEngineer
engineer = FeatureEngineer()
feature_vec = engineer.transform(cleaned)

log("FeatureEngineer", len(feature_vec) == 11, f"length={len(feature_vec)}")
print(f"  Vector: {[round(v, 2) for v in feature_vec]}")
print(f"  Names:  {engineer.feature_names()}")
print(f"  NOTE: The LSTM sees NUMBERS only. It does NOT see process names.")
print(f"        'chrome.exe' identification is done by the REASONING layer.")


# ============================================================================
# STAGE 6: FeatureScaler
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 6: FeatureScaler (raw vector -> [0,1] scaled)")
print("=" * 70)

from backend.preprocessing.scaler import FeatureScaler
scaler = FeatureScaler(model_path="backend/ml/saved_models/feature_scaler.pkl")
scaler.load()

# Single vector (1D) - used during one-at-a-time inference
single_scaled = scaler.transform(feature_vec)
log("Single vector (1D)", single_scaled.shape == (11,), f"shape={single_scaled.shape}")

# Batch matrix (2D) - used by AnomalyDetector when it has 10 timesteps
batch_input = np.array([feature_vec] * 10, dtype=np.float32)
batch_scaled = scaler.transform(batch_input)
log("Batch matrix (10x11)", batch_scaled.shape == (10, 11), f"shape={batch_scaled.shape}")

print(f"  Scaled single: {[round(v, 4) for v in single_scaled]}")


# ============================================================================
# STAGE 7: SequenceBuilder
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 7: SequenceBuilder (N scaled vectors -> 3D sliding windows)")
print("=" * 70)

from backend.preprocessing.sequence_builder import SequenceBuilder
seq_builder = SequenceBuilder(sequence_length=10)

# 20 observations -> (11, 10, 11) sliding windows
sample_matrix = np.random.rand(20, 11).astype(np.float32)
sequences = seq_builder.build(sample_matrix)
log("SequenceBuilder", sequences.shape == (11, 10, 11), f"(20,11)->{sequences.shape}")

# The LSTM sees 10 timesteps at once, like your example:
# Time 1, Time 2, ... Time 10
print(f"  Each window = {sequences.shape[1]} timesteps x {sequences.shape[2]} features")


# ============================================================================
# STAGE 8: LSTM Autoencoder
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 8: LSTM Autoencoder (3D sequence -> reconstruction)")
print("=" * 70)

from backend.ml.models.lstm_autoencoder import LSTMAutoencoder
autoencoder = LSTMAutoencoder(
    timesteps=10, n_features=11,
    model_path="backend/ml/saved_models/lstm_autoencoder.keras"
)

test_seq = np.random.rand(1, 10, 11).astype(np.float32)
reconstructed = autoencoder.reconstruct(test_seq)
log("LSTM reconstruct", reconstructed.shape == (1, 10, 11), f"{test_seq.shape}->{reconstructed.shape}")

rec_error = autoencoder.compute_reconstruction_error(test_seq, reduction="mean")
log("Reconstruction error", isinstance(rec_error, float), f"error={round(rec_error, 6)}")


# ============================================================================
# STAGE 9: Anomaly Detection (FULL live pipeline)
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 9: AnomalyDetector (live events -> anomaly report)")
print("=" * 70)

from backend.ml.anomaly.anomaly_detector import AnomalyDetector
detector = AnomalyDetector()

# Collect 12 REAL live snapshots from your machine
print("  Collecting 12 live snapshots from your system...")
events = []
gen = EventGenerator()
for i in range(12):
    ev = gen.generate(
        CPUCollector().collect(),
        MemoryCollector().collect(),
        DiskCollector().collect(),
        NetworkCollector().collect(),
        ProcessCollector().collect(),
        WindowsEventCollector().collect(),
    )
    events.append(ev)

report = detector.detect_from_events(events)
log("AnomalyDetector", "is_anomaly" in report,
    f"anomaly={report['is_anomaly']}, score={report['anomaly_score']}, "
    f"error={report['reconstruction_error']}, threshold={report['threshold']}")

print(f"\n  The LSTM says: {'ANOMALY DETECTED' if report['is_anomaly'] else 'NORMAL - no anomaly'}")
print(f"  Score={report['anomaly_score']} vs Threshold={report['threshold']}")
if report.get("contributing_features"):
    print(f"\n  Top contributing features (which METRICS are unusual, NOT which process):")
    for f in report["contributing_features"][:3]:
        print(f"    {f['feature']}: {f['contribution_percent']}%")


# ============================================================================
# STAGE 10: Failure Predictor
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 10: FailurePredictor (anomaly + trends -> risk level + TTF)")
print("=" * 70)

from backend.ml.prediction.failure_predictor import FailurePredictor
predictor = FailurePredictor(anomaly_detector=detector)
prediction = predictor.predict(events)

log("FailurePredictor", "risk_level" in prediction,
    f"risk={prediction['risk_level']}, prob={prediction['failure_probability']}, "
    f"TTF={prediction['predicted_time_to_failure_seconds']}s")
print(f"  Affected subsystems: {prediction.get('affected_subsystems')}")
print(f"  Recommendation: {prediction.get('recommended_action')}")


# ============================================================================
# STAGE 11: Inference Engine (unified entry point)
# ============================================================================
print("\n" + "=" * 70)
print("STAGE 11: InferenceEngine (single snapshot -> full report)")
print("=" * 70)

from backend.ml.inference.inference_engine import InferenceEngine
engine = InferenceEngine()

for ev in events:
    result = engine.process_snapshot(ev)

log("InferenceEngine", "risk_level" in result,
    f"risk={result['risk_level']}, buffer={len(engine.event_buffer)}")


# ============================================================================
# WHAT HAPPENS NEXT (your reasoning layer)
# ============================================================================
print("\n" + "=" * 70)
print("WHAT HAPPENS NEXT (NOT in ML layer)")
print("=" * 70)
print("""
  The ML layer ONLY outputs:
    - is_anomaly: True/False
    - anomaly_score: 0.87
    - threshold: 0.30
    - contributing METRICS: memory_percent, cpu_percent, etc.

  It does NOT know:
    - WHICH process caused it (chrome.exe, etc.)
    - WHY it happened
    - WHAT to do about it

  That's the job of YOUR REASONING LAYER:

    anomaly_detector (ML)
          |
          v
    correlation_engine.py   <-- connects anomaly to process/event timeline
          |
          v
    knowledge_graph.py      <-- builds relationship graph (chrome -> high RAM -> slowdown)
          |
          v
    root_cause_engine.py    <-- determines "chrome.exe caused this"
          |
          v
    RAG + LLM               <-- explains it in natural language
          |
          v
    USER sees: "Chrome is consuming too much memory"
""")


# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("PIPELINE TEST SUMMARY")
print("=" * 70)
passed = sum(1 for _, s, _ in results if s)
failed = sum(1 for _, s, _ in results if not s)
total = len(results)
print(f"\n  {PASS} Passed: {passed}/{total}")
print(f"  {FAIL} Failed: {failed}/{total}")

if failed:
    print("\n  Failed stages:")
    for name, status, detail in results:
        if not status:
            print(f"    - {name}: {detail}")
else:
    print("\n  All pipeline stages passed! Full data flow is correct.")
print()
