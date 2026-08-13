import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ConfirmationDialogProps {
	isOpen: boolean;
	title: string;
	message: string;
	confirmLabel?: string;
	cancelLabel?: string;
	onConfirm: () => void;
	onCancel: () => void;
}

export default function ConfirmationDialog({
	isOpen,
	title,
	message,
	confirmLabel = 'Confirm',
	cancelLabel = 'Cancel',
	onConfirm,
	onCancel,
}: ConfirmationDialogProps) {
	if (!isOpen) return null;

	return (
		<div style={styles.overlay}>
			<div style={styles.dialog}>
				<div style={styles.header}>
					<div style={styles.titleRow}>
						<AlertCircle size={20} color="#38bdf8" />
						<h3 style={styles.title}>{title}</h3>
					</div>
					<button type="button" onClick={onCancel} style={styles.closeBtn}>
						<X size={16} color="#94a3b8" />
					</button>
				</div>

				<p style={styles.message}>{message}</p>

				<div style={styles.actions}>
					<button type="button" onClick={onCancel} style={styles.cancelBtn}>
						{cancelLabel}
					</button>
					<button type="button" onClick={onConfirm} style={styles.confirmBtn}>
						{confirmLabel}
					</button>
				</div>
			</div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	overlay: {
		position: 'fixed',
		inset: 0,
		background: 'rgba(0, 0, 0, 0.75)',
		backdropFilter: 'blur(8px)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		zIndex: 9999,
		padding: '20px',
	},
	dialog: {
		width: '100%',
		maxWidth: '420px',
		borderRadius: '20px',
		background: 'rgba(10, 15, 28, 0.95)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		padding: '24px',
		boxShadow: '0 25px 60px rgba(0, 0, 0, 0.6)',
		display: 'flex',
		flexDirection: 'column',
		gap: '16px',
	},
	header: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
	},
	titleRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
	},
	title: {
		margin: 0,
		fontSize: '17px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	closeBtn: {
		background: 'transparent',
		border: 'none',
		cursor: 'pointer',
	},
	message: {
		margin: 0,
		fontSize: '13px',
		color: '#cbd5e1',
		lineHeight: 1.6,
	},
	actions: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'flex-end',
		gap: '12px',
		marginTop: '8px',
	},
	cancelBtn: {
		padding: '10px 18px',
		borderRadius: '12px',
		background: 'rgba(51, 65, 85, 0.5)',
		border: '1px solid rgba(148, 163, 184, 0.2)',
		color: '#cbd5e1',
		fontSize: '13px',
		fontWeight: 600,
		cursor: 'pointer',
	},
	confirmBtn: {
		padding: '10px 20px',
		borderRadius: '12px',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		border: 'none',
		color: '#ffffff',
		fontSize: '13px',
		fontWeight: 700,
		cursor: 'pointer',
		boxShadow: '0 6px 16px rgba(37, 99, 235, 0.35)',
	},
};
