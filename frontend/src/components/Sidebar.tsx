import React, { useEffect, useState } from 'react';
import {
	Home,
	Mic,
	History,
	Settings as SettingsIcon,
	Sparkles,
	User,
	Activity,
	BarChart3,
	Wrench,
} from 'lucide-react';
import { useSYRA } from '../context/SYRAContext';
import SYRAAvatar from './SYRAAvatar';
import { api } from '../services/api';

export default function Sidebar() {
	const {
		activePage,
		setActivePage,
		settings,
		avatarState,
		historyEvents,
	} = useSYRA();

	// Live Metrics State
	const [metrics, setMetrics] = useState({
		cpu: 18,
		ram: 38,
		disk: 45,
	});

	// Poll live metrics every 3 seconds
	useEffect(() => {
		let isMounted = true;
		const fetchLiveMetrics = async () => {
			try {
				const data: any = await api.currentMetrics();
				if (isMounted && data) {
					const cpuVal = data?.cpu?.cpu_percent ?? data?.cpu_percent ?? 18;
					const ramVal = data?.memory?.memory_percent ?? data?.memory_percent ?? 38;
					const diskVal = data?.disk?.disk_percent ?? data?.disk_percent ?? 45;
					setMetrics({
						cpu: Math.round(Number(cpuVal)),
						ram: Math.round(Number(ramVal)),
						disk: Math.round(Number(diskVal)),
					});
				}
			} catch {
				// Keep fallback metrics if backend is busy
			}
		};

		fetchLiveMetrics();
		const interval = setInterval(fetchLiveMetrics, 3000);
		return () => {
			isMounted = false;
			clearInterval(interval);
		};
	}, []);

	const navItems = [
		{ id: 'home', label: 'Home', icon: Home, badge: null },
		{ id: 'analytics', label: 'Analytics', icon: BarChart3, badge: null },
		{ id: 'remediation', label: 'Fix & Approval', icon: Wrench, badge: null },
		{ id: 'voice', label: 'Voice Assistant', icon: Mic, badge: avatarState === 'listening' ? 'LIVE' : null },
		{ id: 'history', label: 'History', icon: History, badge: historyEvents.length > 0 ? historyEvents.length.toString() : null },
		{ id: 'settings', label: 'Settings', icon: SettingsIcon, badge: null },
	] as const;

	return (
		<aside className="syra-sidebar" style={styles.sidebar}>
			{/* Top Branding & Avatar Header */}
			<div className="syra-brand-box" style={styles.brandBox}>
				<div style={styles.avatarWrap}>
					<SYRAAvatar state={avatarState} size={48} />
				</div>
				<div className="syra-brand-text" style={styles.brandText}>
					<div style={styles.brandTitleRow}>
						<span style={styles.brandName}>SYRA</span>
						<span style={styles.brandTag}>AI</span>
					</div>
					<span style={styles.brandSubtitle}>Computer Health Guard</span>
				</div>
			</div>

			{/* Navigation Group */}
			<nav style={styles.navGroup}>
				<div className="syra-nav-label" style={styles.navLabel}>NAVIGATION</div>
				{navItems.map((item) => {
					const IconComponent = item.icon;
					const isActive = activePage === item.id;

					return (
						<button
							key={item.id}
							type="button"
							onClick={() => setActivePage(item.id)}
							className="syra-nav-item"
							style={isActive ? styles.navItemActive : styles.navItem}
						>
							<div style={styles.navItemLeft}>
								<IconComponent size={18} color={isActive ? '#38bdf8' : '#94a3b8'} />
								<span className="syra-nav-item-label">{item.label}</span>
							</div>

							{item.badge && (
								<span
									className="syra-nav-badge"
									style={{
										...styles.badge,
										background: item.badge === 'LIVE' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(30, 41, 59, 0.8)',
										color: item.badge === 'LIVE' ? '#f43f5e' : '#cbd5e1',
										border: item.badge === 'LIVE' ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(148, 163, 184, 0.15)',
									}}
								>
									{item.badge}
								</span>
							)}
						</button>
					);
				})}
			</nav>

			{/* Live Hardware Telemetry Card */}
			<div className="syra-sidebar-metrics" style={styles.metricsCard}>
				<div style={styles.metricsHeader}>
					<div style={styles.metricsTitleWrap}>
						<Sparkles size={15} color="#818cf8" />
						<span style={styles.metricsTitle}>Live Hardware Telemetry</span>
					</div>
					<span style={styles.liveDot} />
				</div>

				<div style={styles.metricsList}>
					{/* CPU Usage */}
					<div style={styles.metricRow}>
						<div style={styles.metricLabelRow}>
							<span style={styles.metricLabel}>CPU Usage</span>
							<span style={styles.cpuValue}>{metrics.cpu}%</span>
						</div>
						<div style={styles.progressBarTrack}>
							<div
								style={{
									...styles.progressBarFill,
									width: `${Math.min(100, Math.max(4, metrics.cpu))}%`,
									background: '#00e5ff',
								}}
							/>
						</div>
					</div>

					{/* Memory Usage */}
					<div style={styles.metricRow}>
						<div style={styles.metricLabelRow}>
							<span style={styles.metricLabel}>Memory Usage</span>
							<span style={styles.memValue}>{metrics.ram}%</span>
						</div>
						<div style={styles.progressBarTrack}>
							<div
								style={{
									...styles.progressBarFill,
									width: `${Math.min(100, Math.max(4, metrics.ram))}%`,
									background: '#f59e0b',
								}}
							/>
						</div>
					</div>

					{/* Disk Space */}
					<div style={styles.metricRow}>
						<div style={styles.metricLabelRow}>
							<span style={styles.metricLabel}>Disk Space</span>
							<span style={styles.diskValue}>{metrics.disk}%</span>
						</div>
						<div style={styles.progressBarTrack}>
							<div
								style={{
									...styles.progressBarFill,
									width: `${Math.min(100, Math.max(4, metrics.disk))}%`,
									background: '#10b981',
								}}
							/>
						</div>
					</div>
				</div>
			</div>

			{/* Bottom User Footer */}
			<div className="syra-user-footer" style={styles.userFooter}>
				<div style={styles.userAvatar}>
					<User size={16} color="#38bdf8" />
				</div>
				<div style={styles.userInfo}>
					<span style={styles.userName}>{settings.assistant.userName}</span>
					<span style={styles.userStatus}>Protected</span>
				</div>
				<Activity size={14} color="#4ade80" />
			</div>
		</aside>
	);
}

const styles: Record<string, React.CSSProperties> = {
	sidebar: {
		width: '240px',
		minWidth: '240px',
		height: 'calc(100vh - 48px)',
		background: 'rgba(10, 15, 28, 0.92)',
		borderRight: '1px solid rgba(56, 189, 248, 0.12)',
		display: 'flex',
		flexDirection: 'column',
		padding: '20px 16px',
		boxSizing: 'border-box',
		justifyContent: 'space-between',
		gap: '20px',
		userSelect: 'none',
	},
	brandBox: {
		display: 'flex',
		alignItems: 'center',
		gap: '12px',
		paddingBottom: '16px',
		borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
	},
	avatarWrap: {
		flexShrink: 0,
	},
	brandText: {
		display: 'flex',
		flexDirection: 'column',
	},
	brandTitleRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '4px',
	},
	brandName: {
		fontSize: '16px',
		fontWeight: 900,
		letterSpacing: '0.05em',
		color: '#f8fafc',
	},
	brandTag: {
		fontSize: '10px',
		fontWeight: 800,
		padding: '1px 5px',
		borderRadius: '5px',
		background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
		color: '#ffffff',
	},
	brandSubtitle: {
		fontSize: '11px',
		color: '#94a3b8',
		fontWeight: 500,
	},
	navGroup: {
		display: 'flex',
		flexDirection: 'column',
		gap: '6px',
		flex: 1,
	},
	navLabel: {
		fontSize: '10px',
		fontWeight: 800,
		letterSpacing: '0.08em',
		color: '#64748b',
		padding: '0 8px 6px',
	},
	navItem: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		padding: '10px 12px',
		borderRadius: '12px',
		background: 'transparent',
		border: '1px solid transparent',
		color: '#94a3b8',
		fontSize: '13px',
		fontWeight: 600,
		cursor: 'pointer',
		transition: 'all 0.2s ease',
		textAlign: 'left',
	},
	navItemActive: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		padding: '10px 12px',
		borderRadius: '12px',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.28)',
		color: '#f8fafc',
		fontSize: '13px',
		fontWeight: 700,
		boxShadow: '0 4px 15px rgba(56, 189, 248, 0.12)',
	},
	navItemLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
	},
	badge: {
		fontSize: '10px',
		fontWeight: 700,
		padding: '2px 7px',
		borderRadius: '8px',
	},
	metricsCard: {
		background: 'rgba(9, 17, 36, 0.95)',
		border: '1px solid rgba(56, 189, 248, 0.12)',
		borderRadius: '16px',
		padding: '14px 16px',
		display: 'flex',
		flexDirection: 'column',
		gap: '12px',
		backdropFilter: 'blur(12px)',
		boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
	},
	metricsHeader: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		paddingBottom: '2px',
	},
	metricsTitleWrap: {
		display: 'flex',
		alignItems: 'center',
		gap: '7px',
	},
	metricsTitle: {
		fontSize: '12.5px',
		fontWeight: 700,
		color: '#f8fafc',
		letterSpacing: '0.01em',
	},
	liveDot: {
		width: '7px',
		height: '7px',
		borderRadius: '50%',
		background: '#10b981',
		boxShadow: '0 0 8px #10b981',
	},
	metricsList: {
		display: 'flex',
		flexDirection: 'column',
		gap: '10px',
	},
	metricRow: {
		display: 'flex',
		flexDirection: 'column',
		gap: '5px',
	},
	metricLabelRow: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
	},
	metricLabel: {
		fontSize: '12px',
		fontWeight: 500,
		color: '#93c5fd',
	},
	cpuValue: {
		fontSize: '13px',
		fontWeight: 700,
		color: '#00e5ff',
	},
	memValue: {
		fontSize: '13px',
		fontWeight: 700,
		color: '#f59e0b',
	},
	diskValue: {
		fontSize: '13px',
		fontWeight: 700,
		color: '#10b981',
	},
	progressBarTrack: {
		width: '100%',
		height: '6px',
		borderRadius: '3px',
		background: '#111d38',
		overflow: 'hidden',
	},
	progressBarFill: {
		height: '100%',
		borderRadius: '3px',
		transition: 'width 0.4s ease',
	},
	userFooter: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		padding: '10px',
		borderRadius: '12px',
		background: 'rgba(15, 23, 42, 0.5)',
		border: '1px solid rgba(148, 163, 184, 0.08)',
	},
	userAvatar: {
		width: '28px',
		height: '28px',
		borderRadius: '8px',
		background: 'rgba(56, 189, 248, 0.15)',
		border: '1px solid rgba(56, 189, 248, 0.3)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	userInfo: {
		display: 'flex',
		flexDirection: 'column',
		flex: 1,
		overflow: 'hidden',
	},
	userName: {
		fontSize: '12px',
		fontWeight: 700,
		color: '#f8fafc',
		whiteSpace: 'nowrap',
		overflow: 'hidden',
		textOverflow: 'ellipsis',
	},
	userStatus: {
		fontSize: '10px',
		color: '#64748b',
	},
};
