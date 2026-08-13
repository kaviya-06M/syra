import React, { useEffect, useState } from 'react';
import { History, ShieldAlert, CheckCircle, Clock, Plus, BarChart2 } from 'lucide-react';

export default function IncidentsPage() {
	const [incidents, setIncidents] = useState<any[]>([]);
	const [stats, setStats] = useState<any>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');

	async function loadIncidentsData() {
		setLoading(true);
		try {
			const [incRes, statsRes] = await Promise.all([
				fetch('/api/history/incidents?limit=20'),
				fetch('/api/history/stats'),
			]);

			if (incRes.ok) {
				const data = await incRes.json();
				setIncidents(data);
			}
			if (statsRes.ok) {
				const sData = await statsRes.json();
				setStats(sData);
			}
		} catch (err: any) {
			setError('Failed to fetch incident history');
		} finally {
			setLoading(false);
		}
	}

	useEffect(() => {
		void loadIncidentsData();
	}, []);

	async function logTestIncident() {
		try {
			await fetch('/api/history/incidents', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					title: 'High CPU anomaly detected on host',
					severity: 'warning',
					resolved: true,
					details: 'Process chrome.exe exceeded 42.5% CPU workload.',
				}),
			});
			await loadIncidentsData();
		} catch {
			// ignore
		}
	}

	return (
		<div style={styles.container}>
			<section style={styles.heroCard}>
				<div style={styles.heroLeft}>
					<div style={styles.iconBox}>
						<History size={24} color="#38bdf8" />
					</div>
					<div>
						<div style={styles.kicker}>HISTORICAL INCIDENT TRAIL</div>
						<h1 style={styles.title}>Incident Log & Telemetry History</h1>
						<p style={styles.description}>
							Review diagnostic events, anomaly triggers, and resolved mitigation actions tracked across host sessions.
						</p>
					</div>
				</div>

				<button type="button" onClick={logTestIncident} style={styles.btnSecondary}>
					<Plus size={16} />
					<span>Log Incident Event</span>
				</button>
			</section>

			{/* Stats Bar */}
			{stats && (
				<div style={styles.statsGrid}>
					<div style={styles.statCard}>
						<div style={styles.statLabel}>Total Incidents</div>
						<div style={{ ...styles.statVal, color: '#38bdf8' }}>{stats.total_incidents}</div>
					</div>
					<div style={styles.statCard}>
						<div style={styles.statLabel}>Resolved Issues</div>
						<div style={{ ...styles.statVal, color: '#4ade80' }}>{stats.resolved}</div>
					</div>
					<div style={styles.statCard}>
						<div style={styles.statLabel}>Unresolved Anomalies</div>
						<div style={{ ...styles.statVal, color: stats.unresolved > 0 ? '#f87171' : '#94a3b8' }}>
							{stats.unresolved}
						</div>
					</div>
				</div>
			)}

			{/* Incidents Table */}
			<section style={styles.card}>
				<div style={styles.cardHeader}>
					<h3 style={styles.cardTitle}>Recent Telemetry Incidents</h3>
					<span style={styles.badge}>{incidents.length} Records</span>
				</div>

				{loading ? (
					<div style={styles.empty}>Loading incident trail...</div>
				) : incidents.length === 0 ? (
					<div style={styles.empty}>
						<CheckCircle size={32} color="#4ade80" style={{ marginBottom: '12px' }} />
						<div style={{ fontWeight: 700, color: '#f1f5f9' }}>No Anomaly Incidents Logged</div>
						<div style={{ color: '#94a3b8', fontSize: '13px' }}>
							Your computer is running with zero reported telemetry incidents.
						</div>
					</div>
				) : (
					<div style={styles.list}>
						{incidents.map((inc, idx) => (
							<div key={inc.id || idx} style={styles.item}>
								<div style={styles.itemLeft}>
									<div
										style={{
											...styles.statusDot,
											background: inc.resolved ? '#4ade80' : '#f87171',
										}}
									/>
									<div>
										<div style={styles.itemTitle}>{inc.title || 'Telemetry Anomaly'}</div>
										<div style={styles.itemDetails}>{inc.details || inc.root_cause || 'No details'}</div>
									</div>
								</div>

								<div style={styles.itemRight}>
									<span style={inc.resolved ? styles.badgeResolved : styles.badgeActive}>
										{inc.resolved ? 'Resolved' : 'Active'}
									</span>
									<div style={styles.timeText}>
										<Clock size={12} />
										<span>{inc.timestamp ? new Date(inc.timestamp).toLocaleTimeString() : 'Recent'}</span>
									</div>
								</div>
							</div>
						))}
					</div>
				)}
			</section>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'grid',
		gap: '20px',
	},
	heroCard: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(10, 20, 38, 0.85)',
		border: '1px solid rgba(56, 189, 248, 0.18)',
		boxShadow: '0 20px 50px rgba(0, 0, 0, 0.35)',
		backdropFilter: 'blur(16px)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '20px',
		flexWrap: 'wrap',
	},
	heroLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
		maxWidth: '650px',
	},
	iconBox: {
		width: '50px',
		height: '50px',
		borderRadius: '14px',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	kicker: {
		fontSize: '11px',
		letterSpacing: '0.12em',
		color: '#38bdf8',
		fontWeight: 700,
	},
	title: {
		margin: '4px 0',
		fontSize: '22px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	description: {
		margin: 0,
		fontSize: '13px',
		color: '#94a3b8',
		lineHeight: 1.5,
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
	statsGrid: {
		display: 'grid',
		gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
		gap: '16px',
	},
	statCard: {
		padding: '18px',
		borderRadius: '16px',
		background: 'rgba(15, 23, 42, 0.75)',
		border: '1px solid rgba(148, 163, 184, 0.12)',
		display: 'flex',
		flexDirection: 'column',
		gap: '6px',
	},
	statLabel: {
		fontSize: '12px',
		color: '#94a3b8',
		textTransform: 'uppercase',
		letterSpacing: '0.05em',
	},
	statVal: {
		fontSize: '26px',
		fontWeight: 800,
	},
	card: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(15, 23, 42, 0.8)',
		border: '1px solid rgba(148, 163, 184, 0.15)',
		display: 'grid',
		gap: '16px',
	},
	cardHeader: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
	},
	cardTitle: {
		margin: 0,
		fontSize: '17px',
		fontWeight: 700,
		color: '#f8fafc',
	},
	badge: {
		fontSize: '12px',
		padding: '2px 10px',
		borderRadius: '12px',
		background: 'rgba(148, 163, 184, 0.1)',
		color: '#94a3b8',
	},
	empty: {
		padding: '40px 20px',
		textAlign: 'center',
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		justifyContent: 'center',
		color: '#94a3b8',
	},
	list: {
		display: 'flex',
		flexDirection: 'column',
		gap: '10px',
	},
	item: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		padding: '14px 18px',
		borderRadius: '14px',
		background: 'rgba(10, 20, 38, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.08)',
		flexWrap: 'wrap',
		gap: '12px',
	},
	itemLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '14px',
	},
	statusDot: {
		width: '10px',
		height: '10px',
		borderRadius: '50%',
		flexShrink: 0,
	},
	itemTitle: {
		fontSize: '14px',
		fontWeight: 700,
		color: '#f1f5f9',
	},
	itemDetails: {
		fontSize: '12px',
		color: '#94a3b8',
		marginTop: '2px',
	},
	itemRight: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
	},
	badgeResolved: {
		padding: '4px 10px',
		borderRadius: '12px',
		background: 'rgba(34, 197, 94, 0.15)',
		color: '#4ade80',
		fontSize: '11px',
		fontWeight: 700,
	},
	badgeActive: {
		padding: '4px 10px',
		borderRadius: '12px',
		background: 'rgba(239, 68, 68, 0.15)',
		color: '#f87171',
		fontSize: '11px',
		fontWeight: 700,
	},
	timeText: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		fontSize: '12px',
		color: '#64748b',
	},
};
