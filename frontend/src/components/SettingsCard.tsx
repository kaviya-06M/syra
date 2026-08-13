import React from 'react';

interface SettingsCardProps {
	title: string;
	description?: string;
	icon: React.ReactNode;
	children: React.ReactNode;
}

export default function SettingsCard({ title, description, icon, children }: SettingsCardProps) {
	return (
		<div style={styles.card}>
			<div style={styles.header}>
				<div style={styles.iconBox}>{icon}</div>
				<div>
					<h3 style={styles.title}>{title}</h3>
					{description && <p style={styles.description}>{description}</p>}
				</div>
			</div>
			<div style={styles.content}>{children}</div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	card: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(15, 23, 42, 0.8)',
		border: '1px solid rgba(148, 163, 184, 0.12)',
		boxShadow: '0 12px 30px rgba(0, 0, 0, 0.25)',
		backdropFilter: 'blur(16px)',
		display: 'flex',
		flexDirection: 'column',
		gap: '20px',
	},
	header: {
		display: 'flex',
		alignItems: 'center',
		gap: '14px',
	},
	iconBox: {
		width: '42px',
		height: '42px',
		borderRadius: '12px',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	title: {
		margin: 0,
		fontSize: '17px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	description: {
		margin: '2px 0 0',
		fontSize: '12px',
		color: '#94a3b8',
	},
	content: {
		display: 'flex',
		flexDirection: 'column',
		gap: '16px',
	},
};
