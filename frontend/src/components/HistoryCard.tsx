import React from 'react';
import { ShieldAlert, CheckCircle2, MessageSquare, AlertCircle } from 'lucide-react';
import { AnomalyEvent } from '../types/types';

interface HistoryCardProps {
	event: AnomalyEvent;
	onViewConversation: (event: AnomalyEvent) => void;
}

export default function HistoryCard({ event, onViewConversation }: HistoryCardProps) {
	return (
		<div style={styles.card}>
			<div style={styles.header}>
				<div>
					<h3 style={styles.title}>{event.title}</h3>
					<span style={styles.timestamp}>{event.timestamp}</span>
				</div>

				<div style={event.resolved ? styles.badgeResolved : styles.badgeActive}>
					{event.resolved ? (
						<>
							<CheckCircle2 size={12} />
							<span>Resolved</span>
						</>
					) : (
						<>
							<ShieldAlert size={12} />
							<span>Active Anomaly</span>
						</>
					)}
				</div>
			</div>

			<div style={styles.grid}>
				<div style={styles.sectionBlock}>
					<div style={styles.sectionLabel}>ROOT CAUSE</div>
					<div style={styles.sectionValue}>{event.rootCause}</div>
				</div>

				<div style={styles.sectionBlock}>
					<div style={styles.sectionLabel}>WHY IT HAPPENED</div>
					<div style={styles.sectionValue}>{event.whyItHappened}</div>
				</div>

				<div style={styles.sectionBlock}>
					<div style={styles.sectionLabel}>RECOMMENDATION</div>
					<div style={styles.sectionValueHighlight}>{event.recommendation}</div>
				</div>

				<div style={styles.sectionBlock}>
					<div style={styles.sectionLabel}>FUTURE RISK</div>
					<div style={styles.sectionValue}>{event.futureRisk}</div>
				</div>
			</div>

			<div style={styles.footer}>
				<button
					type="button"
					onClick={() => onViewConversation(event)}
					style={styles.viewBtn}
				>
					<MessageSquare size={14} />
					<span>View Conversation</span>
				</button>
			</div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	card: {
		padding: '20px',
		borderRadius: '20px',
		background: 'rgba(15, 23, 42, 0.8)',
		border: '1px solid rgba(148, 163, 184, 0.12)',
		boxShadow: '0 12px 30px rgba(0, 0, 0, 0.25)',
		backdropFilter: 'blur(16px)',
		display: 'flex',
		flexDirection: 'column',
		gap: '16px',
	},
	header: {
		display: 'flex',
		alignItems: 'flex-start',
		justifyContent: 'space-between',
		gap: '12px',
	},
	title: {
		margin: 0,
		fontSize: '17px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	timestamp: {
		fontSize: '11px',
		color: '#64748b',
		marginTop: '2px',
		display: 'block',
	},
	badgeResolved: {
		display: 'flex',
		alignItems: 'center',
		gap: '5px',
		padding: '4px 10px',
		borderRadius: '12px',
		background: 'rgba(34, 197, 94, 0.15)',
		border: '1px solid rgba(34, 197, 94, 0.3)',
		color: '#4ade80',
		fontSize: '11px',
		fontWeight: 700,
	},
	badgeActive: {
		display: 'flex',
		alignItems: 'center',
		gap: '5px',
		padding: '4px 10px',
		borderRadius: '12px',
		background: 'rgba(239, 68, 68, 0.15)',
		border: '1px solid rgba(239, 68, 68, 0.3)',
		color: '#f87171',
		fontSize: '11px',
		fontWeight: 700,
	},
	grid: {
		display: 'grid',
		gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
		gap: '14px',
		padding: '16px',
		borderRadius: '14px',
		background: 'rgba(10, 15, 28, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.08)',
	},
	sectionBlock: {
		display: 'flex',
		flexDirection: 'column',
		gap: '4px',
	},
	sectionLabel: {
		fontSize: '10px',
		fontWeight: 800,
		letterSpacing: '0.08em',
		color: '#38bdf8',
		textTransform: 'uppercase',
	},
	sectionValue: {
		fontSize: '13px',
		color: '#cbd5e1',
		lineHeight: 1.5,
	},
	sectionValueHighlight: {
		fontSize: '13px',
		color: '#4ade80',
		fontWeight: 600,
		lineHeight: 1.5,
	},
	footer: {
		display: 'flex',
		justifyContent: 'flex-end',
	},
	viewBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '8px 16px',
		borderRadius: '12px',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.3)',
		color: '#38bdf8',
		fontSize: '12px',
		fontWeight: 600,
		cursor: 'pointer',
		transition: 'all 0.2s ease',
	},
};
