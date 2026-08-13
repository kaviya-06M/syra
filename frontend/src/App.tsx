import React from 'react';
import {
	Cpu,
	Minus,
	Square,
	X,
	Activity,
} from 'lucide-react';
import { SYRAProvider, useSYRA } from './context/SYRAContext';
import DesktopNotification from './components/DesktopNotification';
import SystemTrayStatus from './components/SystemTrayStatus';
import Sidebar from './components/Sidebar';

import WelcomePage from './renderer/pages/WelcomePage';
import HomePage from './renderer/pages/HomePage';
import VoicePage from './renderer/pages/VoicePage';
import HistoryPage from './renderer/pages/HistoryPage';
import SettingsPage from './renderer/pages/SettingsPage';
import AnalyticsPage from './renderer/pages/AnalyticsPage';
import RemediationPage from './renderer/pages/RemediationPage';

function AppContent() {
	const {
		activePage,
		healthState,
		showNotification,
		notificationAnomaly,
		dismissNotification,
		openAnomalyFromNotification,
		setWindowState,
	} = useSYRA();

	const renderActivePage = () => {
		switch (activePage) {
			case 'welcome':
				return <WelcomePage />;
			case 'home':
				return <HomePage />;
			case 'analytics':
				return <AnalyticsPage />;
			case 'remediation':
				return <RemediationPage />;
			case 'voice':
				return <VoicePage />;
			case 'history':
				return <HistoryPage />;
			case 'settings':
				return <SettingsPage />;
			default:
				return <HomePage />;
		}
	};

	const isAnomaly = healthState.status === 'anomaly_detected';

	return (
		<div className="syra-window-frame" style={styles.windowFrame}>
			{/* Electron Desktop Window Titlebar */}
			<header className="syra-titlebar" style={styles.titleBar}>
				<div style={styles.titleLeft}>
					<div style={styles.syraLogo}>
						<Cpu size={15} color="#38bdf8" />
					</div>
					<span style={styles.appTitle}>SYRA AI Assistant</span>
					<span className="syra-app-version" style={styles.appVersion}>v2.4 Desktop</span>
				</div>

				<div className="syra-title-center" style={styles.titleCenter}>
					<div style={styles.statusPill}>
						<Activity size={12} color={isAnomaly ? '#f87171' : '#4ade80'} />
						<span style={{ color: isAnomaly ? '#f87171' : '#cbd5e1' }}>
							{isAnomaly ? 'Anomaly Active · System Alert' : 'Background Telemetry Active'}
						</span>
					</div>
				</div>

				<div style={styles.titleRight}>
					<SystemTrayStatus />

					<div style={styles.windowControls}>
						<button
							type="button"
							onClick={() => setWindowState('minimized')}
							style={styles.winControlBtn}
							title="Minimize"
						>
							<Minus size={13} color="#94a3b8" />
						</button>
						<button
							type="button"
							onClick={() => setWindowState('normal')}
							style={styles.winControlBtn}
							title="Maximize"
						>
							<Square size={11} color="#94a3b8" />
						</button>
						<button
							type="button"
							onClick={() => setWindowState('tray_only')}
							style={{ ...styles.winControlBtn, ...styles.closeBtn }}
							title="Close to Tray"
						>
							<X size={14} color="#94a3b8" />
						</button>
					</div>
				</div>
			</header>

			{/* Desktop Layout Container with Left Sidebar */}
			<div className="syra-app-body" style={styles.appBody}>
				<Sidebar />

				<main className="syra-main-view" style={styles.mainView}>
					{renderActivePage()}
				</main>
			</div>

			{/* Bottom-Left Desktop Anomaly Notification Overlay */}
			<DesktopNotification
				visible={showNotification}
				anomaly={notificationAnomaly}
				onTalkToSyra={openAnomalyFromNotification}
				onDismiss={dismissNotification}
			/>
		</div>
	);
}

export default function App() {
	return (
		<SYRAProvider>
			<AppContent />
		</SYRAProvider>
	);
}

const styles: Record<string, React.CSSProperties> = {
	windowFrame: {
		width: '100%',
		minWidth: 0,
		minHeight: '100%',
		height: '100vh',
		background: '#030712',
		color: '#f8fafc',
		fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
		display: 'flex',
		flexDirection: 'column',
		overflow: 'hidden',
		userSelect: 'none',
	},
	titleBar: {
		height: '48px',
		background: 'rgba(10, 15, 28, 0.98)',
		borderBottom: '1px solid rgba(56, 189, 248, 0.15)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		padding: '0 16px',
		position: 'sticky',
		top: 0,
		zIndex: 1000,
		backdropFilter: 'blur(16px)',
		flexShrink: 0,
	},
	titleLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
	},
	syraLogo: {
		width: '26px',
		height: '26px',
		borderRadius: '8px',
		background: 'rgba(56, 189, 248, 0.15)',
		border: '1px solid rgba(56, 189, 248, 0.3)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
	},
	appTitle: {
		fontSize: '13px',
		fontWeight: 800,
		letterSpacing: '0.04em',
		color: '#f8fafc',
	},
	appVersion: {
		fontSize: '10px',
		color: '#64748b',
		padding: '2px 6px',
		borderRadius: '6px',
		background: 'rgba(30, 41, 59, 0.6)',
	},
	titleCenter: {
		display: 'flex',
		alignItems: 'center',
	},
	statusPill: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '4px 12px',
		borderRadius: '12px',
		background: 'rgba(15, 23, 42, 0.8)',
		border: '1px solid rgba(148, 163, 184, 0.12)',
		fontSize: '11px',
		fontWeight: 600,
	},
	titleRight: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
	},
	windowControls: {
		display: 'flex',
		alignItems: 'center',
		gap: '2px',
	},
	winControlBtn: {
		width: '32px',
		height: '32px',
		borderRadius: '8px',
		background: 'transparent',
		border: 'none',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		cursor: 'pointer',
	},
	closeBtn: {},
	appBody: {
		display: 'flex',
		flex: 1,
		height: 'calc(100vh - 48px)',
		overflow: 'hidden',
		minWidth: 0,
	},
	mainView: {
		flex: 1,
		padding: '24px 28px 40px',
		minWidth: 0,
		minHeight: 0,
		boxSizing: 'border-box',
		overflowY: 'auto',
	},
};
