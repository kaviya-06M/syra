import React from 'react';
import { Volume2, MessageSquare, Bell, Sparkles, ShieldCheck } from 'lucide-react';
import SYRAAvatar from '../../components/SYRAAvatar';
import { useSYRA } from '../../context/SYRAContext';

export default function HomePage() {
	const { setActivePage, healthState, triggerAnomalySimulation, settings, avatarState, speakText, startListening } = useSYRA();
	const hasAnomaly = !!healthState.activeAnomaly;

	const handleTalkToSyra = () => {
		setActivePage('voice');
		startListening();
	};

	const playGreeting = () => {
		speakText(`Hello John, I'm SYRA, your computer health monitor. Everything looks healthy right now. How can I help you?`);
	};

	return (
		<div style={styles.container}>
			{/* Central SYRA Avatar Interaction Area */}
			<div style={styles.avatarSection}>
				<SYRAAvatar
					state={hasAnomaly ? 'alert' : avatarState}
					size={220}
					onClick={handleTalkToSyra}
				/>

				<div style={styles.greetingBox}>
					<div style={styles.greetingHeaderRow}>
						<h2 style={styles.greetingTitle}>
							Hello {settings.assistant.userName} 👋
						</h2>
						<button
							type="button"
							onClick={playGreeting}
							style={styles.speakerBtn}
							title="Replay Voice Greeting"
						>
							<Volume2 size={18} color="#38bdf8" />
						</button>
					</div>

					<p style={styles.greetingSubtitle}>
						I'm SYRA, your computer health monitor.
					</p>

					<div style={hasAnomaly ? styles.statusBoxAlert : styles.statusBoxHealthy}>
						<span style={{ ...styles.statusDot, backgroundColor: hasAnomaly ? '#ef4444' : '#22c55e' }} />
						<span style={{ color: hasAnomaly ? '#f87171' : '#4ade80', fontWeight: 700 }}>
							{hasAnomaly ? '⚠ Issue Detected in Background' : 'Everything looks healthy right now.'}
						</span>
					</div>

					<p style={styles.promptQuestion}>How can I help you today?</p>
				</div>

				{/* Primary Talk Action Button */}
				<button
					type="button"
					onClick={handleTalkToSyra}
					style={styles.talkButton}
				>
					<MessageSquare size={18} />
					<span>Talk to SYRA</span>
					<Sparkles size={16} />
				</button>
			</div>

			{/* Quick Action Bar */}
			<div style={styles.quickBar}>
				<div style={styles.quickItem}>
					<ShieldCheck size={16} color="#38bdf8" />
					<span>Silent Background Guard Active</span>
				</div>

				<div style={styles.quickDivider} />

				<button
					type="button"
					onClick={triggerAnomalySimulation}
					style={styles.testBtn}
				>
					<Bell size={14} color="#facc15" />
					<span>Simulate Background Anomaly</span>
				</button>
			</div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		justifyContent: 'center',
		minHeight: '68vh',
		gap: '32px',
		padding: '20px 0',
	},
	avatarSection: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		textAlign: 'center',
		gap: '24px',
		width: '100%',
		maxWidth: '560px',
	},
	greetingBox: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		gap: '8px',
	},
	greetingHeaderRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
	},
	speakerBtn: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		width: '32px',
		height: '32px',
		borderRadius: '50%',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.28)',
		cursor: 'pointer',
		transition: 'all 0.2s ease',
	},
	greetingTitle: {
		margin: 0,
		fontSize: '28px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	greetingSubtitle: {
		margin: 0,
		fontSize: '15px',
		color: '#94a3b8',
	},
	statusBoxHealthy: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '8px 18px',
		borderRadius: '20px',
		background: 'rgba(34, 197, 94, 0.12)',
		border: '1px solid rgba(34, 197, 94, 0.3)',
		marginTop: '6px',
		fontSize: '13px',
	},
	statusBoxAlert: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '8px 18px',
		borderRadius: '20px',
		background: 'rgba(239, 68, 68, 0.15)',
		border: '1px solid rgba(239, 68, 68, 0.35)',
		marginTop: '6px',
		fontSize: '13px',
	},
	statusDot: {
		width: '8px',
		height: '8px',
		borderRadius: '50%',
		boxShadow: '0 0 8px currentColor',
	},
	promptQuestion: {
		margin: '8px 0 0',
		fontSize: '14px',
		color: '#cbd5e1',
		fontWeight: 500,
	},
	talkButton: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		padding: '14px 32px',
		borderRadius: '20px',
		border: 'none',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		color: '#ffffff',
		fontSize: '15px',
		fontWeight: 700,
		cursor: 'pointer',
		boxShadow: '0 10px 30px rgba(37, 99, 235, 0.4)',
		transition: 'transform 0.2s ease',
	},
	quickBar: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
		padding: '10px 20px',
		borderRadius: '20px',
		background: 'rgba(15, 23, 42, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.1)',
		backdropFilter: 'blur(12px)',
		flexWrap: 'wrap',
		justifyContent: 'center',
	},
	quickItem: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		fontSize: '12px',
		color: '#cbd5e1',
	},
	quickDivider: {
		width: '1px',
		height: '16px',
		background: 'rgba(148, 163, 184, 0.2)',
	},
	testBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		padding: '4px 10px',
		borderRadius: '10px',
		background: 'rgba(234, 179, 8, 0.12)',
		border: '1px solid rgba(234, 179, 8, 0.25)',
		color: '#facc15',
		fontSize: '12px',
		fontWeight: 600,
		cursor: 'pointer',
	},
};
