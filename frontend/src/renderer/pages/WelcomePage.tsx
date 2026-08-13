import React from 'react';
import { motion } from 'motion/react';
import { ShieldCheck, Cpu, Mic, Sparkles, ArrowRight } from 'lucide-react';
import SYRAAvatar from '../../components/SYRAAvatar';
import { useSYRA } from '../../context/SYRAContext';

export default function WelcomePage() {
	const { setActivePage, settings } = useSYRA();

	return (
		<div style={styles.container}>
			<motion.div
				initial={{ opacity: 0, y: 20 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 0.6 }}
				style={styles.heroCard}
			>
				<div style={styles.avatarBox}>
					<SYRAAvatar state="idle" size={200} onClick={() => setActivePage('voice')} />
				</div>

				<div style={styles.badge}>
					<Cpu size={14} color="#38bdf8" />
					<span>DESKTOP AI COMPUTER ASSISTANT v2.4</span>
				</div>

				<h1 style={styles.title}>
					Hello {settings.assistant.userName} 👋<br />
					I'm <span style={styles.syraText}>SYRA</span>
				</h1>

				<p style={styles.subtitle}>
					Your proactive computer health monitor. I continuously supervise background metrics, memory pressure, and core performance—letting you focus on work while keeping your computer running smoothly.
				</p>

				<div style={styles.featureGrid}>
					<div style={styles.featureItem}>
						<div style={styles.featureIcon}>
							<ShieldCheck size={18} color="#38bdf8" />
						</div>
						<div>
							<div style={styles.featureTitle}>Silent Background Guard</div>
							<div style={styles.featureDesc}>Monitors memory leaks and processes without distracting dashboards.</div>
						</div>
					</div>

					<div style={styles.featureItem}>
						<div style={styles.featureIcon}>
							<Mic size={18} color="#a855f7" />
						</div>
						<div>
							<div style={styles.featureTitle}>Voice-First Assistant</div>
							<div style={styles.featureDesc}>Talk to SYRA like a human assistant to diagnose issues instantly.</div>
						</div>
					</div>
				</div>

				<div style={styles.actionRow}>
					<button
						type="button"
						onClick={() => setActivePage('voice')}
						style={styles.primaryBtn}
					>
						<Sparkles size={18} />
						<span>Start SYRA Assistant</span>
						<ArrowRight size={18} />
					</button>

					<button
						type="button"
						onClick={() => setActivePage('home')}
						style={styles.secondaryBtn}
					>
						<span>View Home Overview</span>
					</button>
				</div>
			</motion.div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		minHeight: '72vh',
		padding: '20px',
	},
	heroCard: {
		width: '100%',
		maxWidth: '680px',
		padding: '40px 32px',
		borderRadius: '28px',
		background: 'rgba(10, 15, 28, 0.85)',
		border: '1px solid rgba(56, 189, 248, 0.2)',
		boxShadow: '0 30px 80px rgba(0, 0, 0, 0.5), inset 0 0 40px rgba(56, 189, 248, 0.05)',
		backdropFilter: 'blur(20px)',
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		textAlign: 'center',
		gap: '20px',
	},
	avatarBox: {
		marginBottom: '8px',
	},
	badge: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '6px 14px',
		borderRadius: '20px',
		background: 'rgba(56, 189, 248, 0.1)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		color: '#38bdf8',
		fontSize: '11px',
		fontWeight: 700,
		letterSpacing: '0.08em',
	},
	title: {
		margin: 0,
		fontSize: '32px',
		fontWeight: 800,
		color: '#f8fafc',
		lineHeight: 1.2,
	},
	syraText: {
		background: 'linear-gradient(135deg, #38bdf8 0%, #a855f7 100%)',
		WebkitBackgroundClip: 'text',
		WebkitTextFillColor: 'transparent',
	},
	subtitle: {
		margin: 0,
		fontSize: '14px',
		color: '#94a3b8',
		lineHeight: 1.6,
		maxWidth: '540px',
	},
	featureGrid: {
		display: 'grid',
		gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
		gap: '16px',
		width: '100%',
		marginTop: '8px',
		textAlign: 'left',
	},
	featureItem: {
		display: 'flex',
		gap: '12px',
		padding: '14px 16px',
		borderRadius: '16px',
		background: 'rgba(15, 23, 42, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.08)',
	},
	featureIcon: {
		width: '36px',
		height: '36px',
		borderRadius: '10px',
		background: 'rgba(30, 41, 59, 0.8)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	featureTitle: {
		fontSize: '13px',
		fontWeight: 700,
		color: '#f8fafc',
	},
	featureDesc: {
		fontSize: '11px',
		color: '#94a3b8',
		marginTop: '2px',
		lineHeight: 1.4,
	},
	actionRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '12px',
		marginTop: '12px',
		flexWrap: 'wrap',
		justifyContent: 'center',
	},
	primaryBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		padding: '14px 28px',
		borderRadius: '16px',
		border: 'none',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		color: '#ffffff',
		fontSize: '14px',
		fontWeight: 700,
		cursor: 'pointer',
		boxShadow: '0 10px 30px rgba(37, 99, 235, 0.4)',
	},
	secondaryBtn: {
		padding: '14px 22px',
		borderRadius: '16px',
		background: 'rgba(30, 41, 59, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.15)',
		color: '#cbd5e1',
		fontSize: '14px',
		fontWeight: 600,
		cursor: 'pointer',
	},
};
