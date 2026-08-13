import React, { useState } from 'react';
import { Cpu, ShieldCheck, ShieldAlert, Power, Settings as SettingsIcon, Play, Pause, Bell, MessageSquare } from 'lucide-react';
import { useSYRA } from '../context/SYRAContext';

export default function SystemTrayStatus() {
	const { healthState, setActivePage, triggerAnomalySimulation, updateSettings, settings } = useSYRA();
	const [menuOpen, setMenuOpen] = useState(false);

	const isHealthy = healthState.status === 'healthy';
	const isMonitoring = settings.general.backgroundMonitoring;

	return (
		<div style={styles.trayWrapper}>
			<button
				type="button"
				onClick={() => setMenuOpen(!menuOpen)}
				style={isHealthy ? styles.trayBadgeHealthy : styles.trayBadgeAlert}
				title="SYRA Desktop Agent Tray"
			>
				<Cpu size={14} color={isHealthy ? '#38bdf8' : '#f87171'} />
				<span style={styles.trayText}>SYRA</span>
				<span style={{ ...styles.statusDot, backgroundColor: isHealthy ? '#22c55e' : '#ef4444' }} />
			</button>

			{menuOpen && (
				<>
					<div style={styles.backdrop} onClick={() => setMenuOpen(false)} />
					<div style={styles.trayMenu}>
						<div style={styles.menuHeader}>
							<div style={styles.menuTitleRow}>
								<Cpu size={16} color="#38bdf8" />
								<span style={styles.menuTitle}>SYRA Agent</span>
							</div>
							<span style={styles.menuStatus}>
								{isMonitoring ? 'Monitoring Active' : 'Monitoring Paused'}
							</span>
						</div>

						<div style={styles.divider} />

						<button
							type="button"
							onClick={() => {
								setActivePage('home');
								setMenuOpen(false);
							}}
							style={styles.menuItem}
						>
							<ShieldCheck size={14} color="#38bdf8" />
							<span>Open SYRA App</span>
						</button>

						<button
							type="button"
							onClick={() => {
								setActivePage('voice');
								setMenuOpen(false);
							}}
							style={styles.menuItem}
						>
							<MessageSquare size={14} color="#a855f7" />
							<span>Talk to SYRA Voice</span>
						</button>

						<button
							type="button"
							onClick={() => {
								triggerAnomalySimulation();
								setMenuOpen(false);
							}}
							style={styles.menuItem}
						>
							<Bell size={14} color="#facc15" />
							<span>Simulate Anomaly Alert</span>
						</button>

						<button
							type="button"
							onClick={() => {
								updateSettings({
									general: {
										...settings.general,
										backgroundMonitoring: !isMonitoring,
									},
								});
							}}
							style={styles.menuItem}
						>
							{isMonitoring ? <Pause size={14} color="#f87171" /> : <Play size={14} color="#22c55e" />}
							<span>{isMonitoring ? 'Pause Monitoring' : 'Resume Monitoring'}</span>
						</button>

						<button
							type="button"
							onClick={() => {
								setActivePage('settings');
								setMenuOpen(false);
							}}
							style={styles.menuItem}
						>
							<SettingsIcon size={14} color="#cbd5e1" />
							<span>Settings</span>
						</button>

						<div style={styles.divider} />

						<button
							type="button"
							onClick={() => setMenuOpen(false)}
							style={{ ...styles.menuItem, color: '#f87171' }}
						>
							<Power size={14} color="#f87171" />
							<span>Exit SYRA Agent</span>
						</button>
					</div>
				</>
			)}
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	trayWrapper: {
		position: 'relative',
	},
	trayBadgeHealthy: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		padding: '4px 10px',
		borderRadius: '12px',
		background: 'rgba(15, 23, 42, 0.8)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		cursor: 'pointer',
		userSelect: 'none',
	},
	trayBadgeAlert: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		padding: '4px 10px',
		borderRadius: '12px',
		background: 'rgba(239, 68, 68, 0.15)',
		border: '1px solid rgba(239, 68, 68, 0.4)',
		cursor: 'pointer',
		userSelect: 'none',
	},
	trayText: {
		fontSize: '11px',
		fontWeight: 700,
		color: '#f8fafc',
		letterSpacing: '0.05em',
	},
	statusDot: {
		width: '6px',
		height: '6px',
		borderRadius: '50%',
	},
	backdrop: {
		position: 'fixed',
		inset: 0,
		zIndex: 998,
	},
	trayMenu: {
		position: 'absolute',
		top: '120%',
		right: 0,
		width: '210px',
		padding: '8px',
		borderRadius: '14px',
		background: 'rgba(10, 15, 28, 0.95)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6)',
		backdropFilter: 'blur(16px)',
		zIndex: 999,
		display: 'flex',
		flexDirection: 'column',
		gap: '2px',
	},
	menuHeader: {
		padding: '8px 10px',
		display: 'flex',
		flexDirection: 'column',
		gap: '2px',
	},
	menuTitleRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
	},
	menuTitle: {
		fontSize: '12px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	menuStatus: {
		fontSize: '10px',
		color: '#94a3b8',
	},
	divider: {
		height: '1px',
		background: 'rgba(148, 163, 184, 0.15)',
		margin: '4px 0',
	},
	menuItem: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '8px 10px',
		borderRadius: '8px',
		background: 'transparent',
		border: 'none',
		color: '#e2e8f0',
		fontSize: '12px',
		fontWeight: 500,
		cursor: 'pointer',
		textAlign: 'left',
		width: '100%',
	},
};
