import React, { useState } from 'react';
import { Settings as SettingsIcon, Sliders, Mic, Bot, Bell, Shield, Trash2, Check } from 'lucide-react';
import SettingsCard from '../../components/SettingsCard';
import ConfirmationDialog from '../../components/ConfirmationDialog';
import { useSYRA } from '../../context/SYRAContext';

export default function SettingsPage() {
	const { settings, updateSettings, clearMessages } = useSYRA();
	const [showClearDialog, setShowClearDialog] = useState(false);
	const [savedToast, setSavedToast] = useState(false);

	const handleSaveFeedback = () => {
		setSavedToast(true);
		setTimeout(() => setSavedToast(false), 2000);
	};

	return (
		<div style={styles.container}>
			<div style={styles.pageHeader}>
				<div>
					<h2 style={styles.pageTitle}>SYRA Desktop Settings</h2>
					<p style={styles.pageSubtitle}>
						Customize background monitoring, voice assistant options, and notification preferences.
					</p>
				</div>

				{savedToast && (
					<div style={styles.toast}>
						<Check size={14} color="#4ade80" />
						<span>Preferences Updated</span>
					</div>
				)}
			</div>

			<div style={styles.grid}>
				{/* General Settings */}
				<SettingsCard
					title="General System Behavior"
					description="Configure background startup and silent agent preferences"
					icon={<Sliders size={20} color="#38bdf8" />}
				>
					<div style={styles.settingRow}>
						<div>
							<div style={styles.label}>Start SYRA on computer boot</div>
							<div style={styles.sublabel}>Launch silent background monitor when your OS boots</div>
						</div>
						<input
							type="checkbox"
							checked={settings.general.startOnBoot}
							onChange={(e) => {
								updateSettings({ general: { ...settings.general, startOnBoot: e.target.checked } });
								handleSaveFeedback();
							}}
							style={styles.toggle}
						/>
					</div>

					<div style={styles.settingRow}>
						<div>
							<div style={styles.label}>Enable silent background monitoring</div>
							<div style={styles.sublabel}>Supervise memory leaks and hardware pressure without popups</div>
						</div>
						<input
							type="checkbox"
							checked={settings.general.backgroundMonitoring}
							onChange={(e) => {
								updateSettings({ general: { ...settings.general, backgroundMonitoring: e.target.checked } });
								handleSaveFeedback();
							}}
							style={styles.toggle}
						/>
					</div>

					<div style={styles.settingRow}>
						<div>
							<div style={styles.label}>Enable desktop notifications</div>
							<div style={styles.sublabel}>Show small non-intrusive alert popups on anomaly detection</div>
						</div>
						<input
							type="checkbox"
							checked={settings.general.desktopNotifications}
							onChange={(e) => {
								updateSettings({ general: { ...settings.general, desktopNotifications: e.target.checked } });
								handleSaveFeedback();
							}}
							style={styles.toggle}
						/>
					</div>
				</SettingsCard>

				{/* Voice Settings */}
				<SettingsCard
					title="Voice & Audio Engine"
					description="Adjust speech synthesis rates and microphone input settings"
					icon={<Mic size={20} color="#a855f7" />}
				>
					<div style={styles.fieldGroup}>
						<label style={styles.label}>Microphone Device</label>
						<select
							value={settings.voice.microphoneId}
							onChange={(e) => {
								updateSettings({ voice: { ...settings.voice, microphoneId: e.target.value } });
								handleSaveFeedback();
							}}
							style={styles.select}
						>
							<option value="default">Default System Microphone (Array)</option>
							<option value="mic-usb">High Definition USB Studio Mic</option>
						</select>
					</div>

					<div style={styles.fieldGroup}>
						<label style={styles.label}>Speech Speed ({settings.voice.speed}x)</label>
						<input
							type="range"
							min="0.75"
							max="1.5"
							step="0.05"
							value={settings.voice.speed}
							onChange={(e) => {
								updateSettings({ voice: { ...settings.voice, speed: parseFloat(e.target.value) } });
								handleSaveFeedback();
							}}
							style={styles.slider}
						/>
					</div>

					<div style={styles.fieldGroup}>
						<label style={styles.label}>Voice Volume ({Math.round(settings.voice.volume * 100)}%)</label>
						<input
							type="range"
							min="0"
							max="1"
							step="0.05"
							value={settings.voice.volume}
							onChange={(e) => {
								updateSettings({ voice: { ...settings.voice, volume: parseFloat(e.target.value) } });
								handleSaveFeedback();
							}}
							style={styles.slider}
						/>
					</div>
				</SettingsCard>

				{/* Assistant Settings */}
				<SettingsCard
					title="Assistant Persona & Style"
					description="Tailor how SYRA greets and speaks with you"
					icon={<Bot size={20} color="#38bdf8" />}
				>
					<div style={styles.fieldGroup}>
						<label style={styles.label}>Your Name</label>
						<input
							type="text"
							value={settings.assistant.userName}
							onChange={(e) => {
								updateSettings({ assistant: { ...settings.assistant, userName: e.target.value } });
								handleSaveFeedback();
							}}
							style={styles.input}
						/>
					</div>

					<div style={styles.fieldGroup}>
						<label style={styles.label}>Response Style</label>
						<select
							value={settings.assistant.responseStyle}
							onChange={(e) => {
								updateSettings({
									assistant: { ...settings.assistant, responseStyle: e.target.value as any },
								});
								handleSaveFeedback();
							}}
							style={styles.select}
						>
							<option value="conversational">Conversational (Natural & Friendly)</option>
							<option value="concise">Concise (Direct Action Items)</option>
							<option value="detailed">Detailed (Thorough Explanations)</option>
						</select>
					</div>
				</SettingsCard>

				{/* Notifications */}
				<SettingsCard
					title="Notification Overlay"
					description="Configure position and sound cues for desktop alerts"
					icon={<Bell size={20} color="#facc15" />}
				>
					<div style={styles.settingRow}>
						<div>
							<div style={styles.label}>Play alert audio chime</div>
							<div style={styles.sublabel}>Subtle futuristic notification sound</div>
						</div>
						<input
							type="checkbox"
							checked={settings.notifications.soundEnabled}
							onChange={(e) => {
								updateSettings({ notifications: { ...settings.notifications, soundEnabled: e.target.checked } });
								handleSaveFeedback();
							}}
							style={styles.toggle}
						/>
					</div>

					<div style={styles.fieldGroup}>
						<label style={styles.label}>Notification Screen Position</label>
						<select
							value={settings.general.notificationPosition}
							onChange={(e) => {
								updateSettings({ general: { ...settings.general, notificationPosition: e.target.value as any } });
								handleSaveFeedback();
							}}
							style={styles.select}
						>
							<option value="bottom-left">Bottom Left (Recommended Desktop Assistant Style)</option>
							<option value="bottom-right">Bottom Right</option>
							<option value="top-right">Top Right</option>
						</select>
					</div>
				</SettingsCard>

				{/* Privacy & Data */}
				<SettingsCard
					title="Privacy & Local Storage"
					description="SYRA processes system metrics 100% locally on your machine"
					icon={<Shield size={20} color="#34d399" />}
				>
					<div style={styles.privacyNote}>
						<Shield size={16} color="#34d399" />
						<span>All health telemetry and voice transcripts remain stored locally in your encrypted app folder.</span>
					</div>

					<div style={styles.settingRow}>
						<button
							type="button"
							onClick={() => setShowClearDialog(true)}
							style={styles.dangerBtn}
						>
							<Trash2 size={15} />
							<span>Clear Current Conversation Transcript</span>
						</button>
					</div>
				</SettingsCard>
			</div>

			<ConfirmationDialog
				isOpen={showClearDialog}
				title="Clear Voice Transcript"
				message="Are you sure you want to clear the active conversation transcript? Historical incident records will remain saved in History."
				confirmLabel="Clear Transcript"
				onConfirm={() => {
					clearMessages();
					setShowClearDialog(false);
				}}
				onCancel={() => setShowClearDialog(false)}
			/>
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
	pageHeader: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '16px',
	},
	pageTitle: {
		margin: 0,
		fontSize: '22px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	pageSubtitle: {
		margin: '4px 0 0',
		fontSize: '13px',
		color: '#94a3b8',
	},
	toast: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '6px 14px',
		borderRadius: '12px',
		background: 'rgba(34, 197, 94, 0.15)',
		border: '1px solid rgba(34, 197, 94, 0.3)',
		color: '#4ade80',
		fontSize: '12px',
		fontWeight: 600,
	},
	grid: {
		display: 'grid',
		gap: '20px',
	},
	settingRow: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '16px',
	},
	label: {
		fontSize: '13px',
		fontWeight: 700,
		color: '#f8fafc',
	},
	sublabel: {
		fontSize: '11px',
		color: '#94a3b8',
		marginTop: '2px',
	},
	toggle: {
		width: '20px',
		height: '20px',
		accentColor: '#38bdf8',
		cursor: 'pointer',
	},
	fieldGroup: {
		display: 'flex',
		flexDirection: 'column',
		gap: '6px',
	},
	input: {
		padding: '10px 14px',
		borderRadius: '12px',
		background: 'rgba(10, 15, 28, 0.8)',
		border: '1px solid rgba(148, 163, 184, 0.2)',
		color: '#f8fafc',
		fontSize: '13px',
		outline: 'none',
	},
	select: {
		padding: '10px 14px',
		borderRadius: '12px',
		background: 'rgba(10, 15, 28, 0.8)',
		border: '1px solid rgba(148, 163, 184, 0.2)',
		color: '#f8fafc',
		fontSize: '13px',
		outline: 'none',
		cursor: 'pointer',
	},
	slider: {
		accentColor: '#38bdf8',
		cursor: 'pointer',
	},
	privacyNote: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		padding: '12px 16px',
		borderRadius: '14px',
		background: 'rgba(52, 211, 153, 0.1)',
		border: '1px solid rgba(52, 211, 153, 0.25)',
		color: '#6ee7b7',
		fontSize: '12px',
	},
	dangerBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '10px 18px',
		borderRadius: '12px',
		background: 'rgba(239, 68, 68, 0.15)',
		border: '1px solid rgba(239, 68, 68, 0.3)',
		color: '#f87171',
		fontSize: '12px',
		fontWeight: 600,
		cursor: 'pointer',
	},
};
