export type AvatarState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'alert' | 'monitoring';

export type PageType = 'welcome' | 'home' | 'analytics' | 'remediation' | 'voice' | 'history' | 'settings';

export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';

export interface AnomalyEvent {
	id: string;
	title: string;
	summary: string;
	severity: AnomalySeverity;
	timestamp: string;
	resolved: boolean;
	rootCause: string;
	whyItHappened: string;
	recommendation: string;
	futureRisk: string;
	dialogueHistory: Message[];
}

export interface Message {
	id: string;
	sender: 'syra' | 'user';
	text: string;
	timestamp: string;
	suggestedPrompts?: string[];
}

export interface SystemSettings {
	general: {
		startOnBoot: boolean;
		backgroundMonitoring: boolean;
		desktopNotifications: boolean;
		notificationPosition: 'bottom-left' | 'bottom-right' | 'top-right';
	};
	voice: {
		enabled: boolean;
		microphoneId: string;
		voiceName: string;
		speed: number;
		volume: number;
		autoSpeakResponse: boolean;
	};
	assistant: {
		userName: string;
		assistantName: string;
		greetingPreference: string;
		responseStyle: 'conversational' | 'concise' | 'detailed';
	};
	notifications: {
		enableAnomalyAlerts: boolean;
		soundEnabled: boolean;
		flashTrayIcon: boolean;
	};
	privacy: {
		localOnlyProcessing: boolean;
		keepHistoryDays: number;
	};
}

export interface SystemHealthState {
	status: 'healthy' | 'anomaly_detected' | 'analyzing' | 'remediating';
	activeAnomaly: AnomalyEvent | null;
	lastScanTime: string;
	backgroundMonitoringActive: boolean;
}
