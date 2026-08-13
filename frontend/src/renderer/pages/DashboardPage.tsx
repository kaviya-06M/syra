import React from 'react';
import { AlertTriangle, CheckCircle, ShieldAlert, Sparkles, ArrowRight, Activity, Terminal } from 'lucide-react';
import TelemetryCards from '../components/TelemetryCards';
import ProcessTable from '../components/ProcessTable';

interface DashboardPageProps {
	metrics: any;
	diagnosis: any;
	onRunDiagnosis: () => void;
	isDiagnosing: boolean;
	onNavigate: (tab: 'chat' | 'remediation' | 'incidents') => void;
}

export default function DashboardPage({
	metrics,
	diagnosis,
	onRunDiagnosis,
	isDiagnosing,
	onNavigate,
}: DashboardPageProps) {
	const rootCause = diagnosis?.root_cause || 'System operating normally';
	const isAnomaly = rootCause && !rootCause.includes('normally');
	const confidencePercent = diagnosis?.confidence ? Math.round(diagnosis.confidence * 100) : 98;

	return (
		<div style={styles.container}>
			{/* Real-time Diagnosis Banner */}
			<section style={{ ...styles.diagnosisCard, borderColor: isAnomaly ? 'rgba(248, 113, 113, 0.35)' : 'rgba(52, 211, 153, 0.25)' }}>
				<div style={styles.diagnosisTop}>
					<div style={styles.diagnosisStatusLeft}>
						<div
							style={{
								...styles.diagnosisIconBox,
								background: isAnomaly ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
								color: isAnomaly ? '#f87171' : '#4ade80',
							}}
						>
							{isAnomaly ? <ShieldAlert size={24} /> : <CheckCircle size={24} />}
						</div>
						<div>
							<div style={styles.diagnosisKicker}>
								SYRA TELEMETRY DIAGNOSIS • {confidencePercent}% CONFIDENCE
							</div>
							<h2 style={styles.diagnosisTitle}>{rootCause}</h2>
						</div>
					</div>

					<div style={styles.diagnosisActions}>
						<button
							type="button"
							onClick={onRunDiagnosis}
							disabled={isDiagnosing}
							style={styles.btnSecondary}
						>
							<Sparkles size={15} />
							<span>{isDiagnosing ? 'Analyzing...' : 'Run Full AI Scan'}</span>
						</button>

						{isAnomaly && (
							<button
								type="button"
								onClick={() => onNavigate('remediation')}
								style={styles.btnPrimary}
							>
								<span>Resolve with SYRA</span>
								<ArrowRight size={15} />
							</button>
						)}
					</div>
				</div>

				{diagnosis?.evidence && diagnosis.evidence.length > 0 && (
					<div style={styles.evidenceRow}>
						<span style={styles.evidenceLabel}>Telemetry Evidence:</span>
						{diagnosis.evidence.map((ev: string, idx: number) => (
							<span key={idx} style={styles.evidenceChip}>
								{ev}
							</span>
						))}
					</div>
				)}
			</section>

			{/* Telemetry Metric Meters */}
			<div>
				<div style={styles.sectionHeader}>
					<Activity size={18} color="#38bdf8" />
					<span style={styles.sectionTitle}>Real-time System Metrics</span>
				</div>
				<TelemetryCards metrics={metrics} />
			</div>

			{/* Active Processes */}
			<div>
				<div style={styles.sectionHeader}>
					<Terminal size={18} color="#a855f7" />
					<span style={styles.sectionTitle}>System Process Inspector</span>
				</div>
				<ProcessTable
					topCpu={metrics?.processes?.top_cpu || []}
					topMemory={metrics?.processes?.top_memory || []}
				/>
			</div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'grid',
		gap: '24px',
	},
	diagnosisCard: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(10, 20, 38, 0.85)',
		border: '1px solid',
		boxShadow: '0 20px 50px rgba(0, 0, 0, 0.35)',
		backdropFilter: 'blur(16px)',
		display: 'grid',
		gap: '16px',
	},
	diagnosisTop: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '16px',
		flexWrap: 'wrap',
	},
	diagnosisStatusLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
	},
	diagnosisIconBox: {
		width: '52px',
		height: '52px',
		borderRadius: '16px',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	diagnosisKicker: {
		fontSize: '11px',
		letterSpacing: '0.12em',
		textTransform: 'uppercase',
		color: '#94a3b8',
		fontWeight: 700,
	},
	diagnosisTitle: {
		margin: '4px 0 0',
		fontSize: '20px',
		fontWeight: 700,
		color: '#f8fafc',
	},
	diagnosisActions: {
		display: 'flex',
		alignItems: 'center',
		gap: '12px',
	},
	btnPrimary: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '10px 20px',
		borderRadius: '12px',
		border: 'none',
		background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
		color: '#fff',
		fontWeight: 700,
		fontSize: '13px',
		cursor: 'pointer',
		boxShadow: '0 8px 20px rgba(239, 68, 68, 0.3)',
	},
	btnSecondary: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '10px 18px',
		borderRadius: '12px',
		border: '1px solid rgba(56, 189, 248, 0.3)',
		background: 'rgba(56, 189, 248, 0.12)',
		color: '#38bdf8',
		fontWeight: 600,
		fontSize: '13px',
		cursor: 'pointer',
	},
	evidenceRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		flexWrap: 'wrap',
		paddingTop: '12px',
		borderTop: '1px solid rgba(148, 163, 184, 0.1)',
	},
	evidenceLabel: {
		fontSize: '12px',
		color: '#94a3b8',
		fontWeight: 600,
	},
	evidenceChip: {
		fontSize: '12px',
		padding: '4px 10px',
		borderRadius: '8px',
		background: 'rgba(30, 41, 59, 0.8)',
		color: '#cbd5e1',
		border: '1px solid rgba(148, 163, 184, 0.15)',
	},
	sectionHeader: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		marginBottom: '14px',
	},
	sectionTitle: {
		fontSize: '16px',
		fontWeight: 700,
		color: '#f8fafc',
	},
};
