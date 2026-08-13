import { SystemSettings } from '../types/types';

export const defaultSettings: SystemSettings = {
	general: {
		startOnBoot: true,
		backgroundMonitoring: true,
		desktopNotifications: true,
		notificationPosition: 'bottom-left',
	},
	voice: {
		enabled: true,
		microphoneId: 'default',
		voiceName: 'SYRA AI Voice (English UK Neural)',
		speed: 1.0,
		volume: 0.9,
		autoSpeakResponse: true,
	},
	assistant: {
		userName: 'John',
		assistantName: 'SYRA',
		greetingPreference: 'Warm & Professional',
		responseStyle: 'conversational',
	},
	notifications: {
		enableAnomalyAlerts: true,
		soundEnabled: true,
		flashTrayIcon: true,
	},
	privacy: {
		localOnlyProcessing: true,
		keepHistoryDays: 30,
	},
};

