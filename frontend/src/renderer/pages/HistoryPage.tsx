import React from 'react';
import { History, ShieldCheck, MessageSquare } from 'lucide-react';
import HistoryCard from '../../components/HistoryCard';
import { useSYRA } from '../../context/SYRAContext';
import { AnomalyEvent } from '../../types/types';

export default function HistoryPage() {
	const { historyEvents, setActivePage, setSelectedHistoryEvent } = useSYRA();

	const handleViewConversation = (event: AnomalyEvent) => {
		setSelectedHistoryEvent(event);
		setActivePage('voice');
	};

	return (
		<div style={styles.container}>
			<div style={styles.headerBox}>
				<div style={styles.headerLeft}>
					<div style={styles.iconBox}>
						<History size={22} color="#38bdf8" />
					</div>
					<div>
						<h2 style={styles.title}>Incident & Conversation Memory</h2>
						<p style={styles.subtitle}>
							Review past computer health incidents, root cause explanations, recommendations, and saved conversations.
						</p>
					</div>
				</div>

				<div style={styles.countBadge}>
					<span>{historyEvents.length} Events Recorded</span>
				</div>
			</div>

			<div style={styles.list}>
				{historyEvents.length === 0 ? (
					<div style={styles.emptyBox}>
						<ShieldCheck size={36} color="#4ade80" />
						<div style={styles.emptyTitle}>No Historical Anomalies</div>
						<p style={styles.emptySubtitle}>
							Your computer has maintained clean system health with zero reported incident events.
						</p>
					</div>
				) : (
					historyEvents.map((event) => (
						<HistoryCard
							key={event.id}
							event={event}
							onViewConversation={handleViewConversation}
						/>
					))
				)}
			</div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'grid',
		gap: '24px',
		width: '100%',
		maxWidth: '860px',
		margin: '0 auto',
	},
	headerBox: {
		padding: '24px',
		borderRadius: '24px',
		background: 'rgba(10, 15, 28, 0.85)',
		border: '1px solid rgba(56, 189, 248, 0.18)',
		backdropFilter: 'blur(16px)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '16px',
		flexWrap: 'wrap',
	},
	headerLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
	},
	iconBox: {
		width: '46px',
		height: '46px',
		borderRadius: '14px',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	title: {
		margin: 0,
		fontSize: '20px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	subtitle: {
		margin: '4px 0 0',
		fontSize: '13px',
		color: '#94a3b8',
	},
	countBadge: {
		padding: '6px 14px',
		borderRadius: '14px',
		background: 'rgba(30, 41, 59, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.12)',
		color: '#cbd5e1',
		fontSize: '12px',
		fontWeight: 600,
	},
	list: {
		display: 'grid',
		gap: '20px',
	},
	emptyBox: {
		padding: '48px 24px',
		borderRadius: '24px',
		background: 'rgba(15, 23, 42, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.1)',
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		textAlign: 'center',
		gap: '12px',
	},
	emptyTitle: {
		fontSize: '18px',
		fontWeight: 700,
		color: '#f8fafc',
	},
	emptySubtitle: {
		margin: 0,
		fontSize: '13px',
		color: '#94a3b8',
		maxWidth: '420px',
	},
};
