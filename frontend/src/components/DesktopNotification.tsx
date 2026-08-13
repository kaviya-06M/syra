import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ShieldAlert, X, MessageSquare } from 'lucide-react';
import { AnomalyEvent } from '../types/types';

interface DesktopNotificationProps {
	visible: boolean;
	anomaly: AnomalyEvent | null;
	onTalkToSyra: () => void;
	onDismiss: () => void;
}

export default function DesktopNotification({
	visible,
	anomaly,
	onTalkToSyra,
	onDismiss,
}: DesktopNotificationProps) {
	return (
		<AnimatePresence>
			{visible && (
				<motion.div
					initial={{ x: -320, opacity: 0, scale: 0.95 }}
					animate={{ x: 0, opacity: 1, scale: 1 }}
					exit={{ x: -320, opacity: 0, scale: 0.95 }}
					transition={{ type: 'spring', stiffness: 350, damping: 25 }}
					style={styles.notificationWindow}
				>
					{/* Windows OS Notification Header */}
					<div style={styles.header}>
						<div style={styles.brandGroup}>
							<div style={styles.appDot} />
							<span style={styles.appName}>SYRA</span>
							<span style={styles.timeTag}>Just now</span>
						</div>
						<button type="button" onClick={onDismiss} style={styles.closeBtn} title="Dismiss">
							<X size={14} color="#94a3b8" />
						</button>
					</div>

					{/* Notification Body */}
					<div style={styles.body}>
						<div style={styles.alertIconBox}>
							<ShieldAlert size={20} color="#f87171" />
						</div>
						<div style={styles.textContainer}>
							<div style={styles.alertTitle}>⚠ Something unusual detected</div>
							<p style={styles.alertDescription}>
								I noticed an issue while monitoring your computer.
							</p>
						</div>
					</div>

					{/* Action Footer Button */}
					<button type="button" onClick={onTalkToSyra} style={styles.actionBtn}>
						<MessageSquare size={14} />
						<span>Talk to SYRA</span>
					</button>
				</motion.div>
			)}
		</AnimatePresence>
	);
}

const styles: Record<string, React.CSSProperties> = {
	notificationWindow: {
		position: 'fixed',
		bottom: '24px',
		left: '24px',
		width: '320px',
		padding: '16px',
		borderRadius: '18px',
		background: 'rgba(10, 15, 28, 0.95)',
		border: '1px solid rgba(248, 113, 113, 0.35)',
		boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 20px rgba(239, 68, 68, 0.15)',
		backdropFilter: 'blur(20px)',
		zIndex: 9999,
		display: 'flex',
		flexDirection: 'column',
		gap: '12px',
		userSelect: 'none',
	},
	header: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
	},
	brandGroup: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
	},
	appDot: {
		width: '8px',
		height: '8px',
		borderRadius: '50%',
		background: '#38bdf8',
		boxShadow: '0 0 8px #38bdf8',
	},
	appName: {
		fontSize: '11px',
		fontWeight: 800,
		letterSpacing: '0.1em',
		color: '#f8fafc',
	},
	timeTag: {
		fontSize: '10px',
		color: '#64748b',
	},
	closeBtn: {
		background: 'transparent',
		border: 'none',
		cursor: 'pointer',
		padding: '2px',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
	},
	body: {
		display: 'flex',
		gap: '12px',
		alignItems: 'flex-start',
	},
	alertIconBox: {
		width: '36px',
		height: '36px',
		borderRadius: '12px',
		background: 'rgba(239, 68, 68, 0.15)',
		border: '1px solid rgba(239, 68, 68, 0.3)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	textContainer: {
		display: 'flex',
		flexDirection: 'column',
		gap: '2px',
	},
	alertTitle: {
		fontSize: '13px',
		fontWeight: 700,
		color: '#f8fafc',
	},
	alertDescription: {
		margin: 0,
		fontSize: '12px',
		color: '#cbd5e1',
		lineHeight: 1.4,
	},
	actionBtn: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		gap: '8px',
		padding: '10px 16px',
		borderRadius: '12px',
		border: 'none',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		color: '#ffffff',
		fontSize: '12px',
		fontWeight: 700,
		cursor: 'pointer',
		boxShadow: '0 6px 16px rgba(37, 99, 235, 0.35)',
		transition: 'transform 0.15s ease',
	},
};
