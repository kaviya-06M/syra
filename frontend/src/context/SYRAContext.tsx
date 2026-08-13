import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
	AvatarState,
	PageType,
	AnomalyEvent,
	Message,
	SystemSettings,
	SystemHealthState,
} from '../types/types';
import { defaultSettings } from '../data/mockData';
import { api } from '../services/api';

let chatSessionId: string | undefined;

interface SYRAContextType {
	activePage: PageType;
	setActivePage: (page: PageType) => void;
	avatarState: AvatarState;
	setAvatarState: (state: AvatarState) => void;
	settings: SystemSettings;
	updateSettings: (newSettings: Partial<SystemSettings>) => void;
	healthState: SystemHealthState;
	showNotification: boolean;
	notificationAnomaly: AnomalyEvent | null;
	triggerAnomalySimulation: () => void;
	dismissNotification: () => void;
	openAnomalyFromNotification: () => void;
	messages: Message[];
	sendMessage: (text: string) => void;
	clearMessages: () => void;
	historyEvents: AnomalyEvent[];
	selectedHistoryEvent: AnomalyEvent | null;
	setSelectedHistoryEvent: (event: AnomalyEvent | null) => void;
	isListening: boolean;
	isSpeaking: boolean;
	isThinking: boolean;
	startListening: () => void;
	stopListening: () => void;
	speakText: (text: string) => void;
	stopSpeaking: () => void;
	windowState: 'normal' | 'minimized' | 'tray_only';
	setWindowState: (state: 'normal' | 'minimized' | 'tray_only') => void;
	resolveActiveAnomaly: () => void;
	recordExecutedRemediation: (params: {
		action: string;
		rootCause: string;
		message?: string;
		resolved?: boolean;
		before?: any;
		after?: any;
	}) => void;
	refreshHistory: () => Promise<void>;
}

const SYRAContext = createContext<SYRAContextType | undefined>(undefined);

export const SYRAProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const [activePage, setActivePage] = useState<PageType>('home');
	const [avatarState, setAvatarState] = useState<AvatarState>('idle');
	const [settings, setSettings] = useState<SystemSettings>(defaultSettings);
	const [historyEvents, setHistoryEvents] = useState<AnomalyEvent[]>(() => {
		try {
			const saved = localStorage.getItem('syra_history_events');
			return saved ? JSON.parse(saved) : [];
		} catch {
			return [];
		}
	});
	const [selectedHistoryEvent, setSelectedHistoryEvent] = useState<AnomalyEvent | null>(null);

	const [activeAnomaly, setActiveAnomaly] = useState<AnomalyEvent | null>(null);
	const [showNotification, setShowNotification] = useState<boolean>(false);
	const [notificationAnomaly, setNotificationAnomaly] = useState<AnomalyEvent | null>(null);

	const [messages, setMessages] = useState<Message[]>([
		{
			id: 'welcome-1',
			sender: 'syra',
			text: `Hello John, I'm SYRA, your computer health monitor. Everything looks healthy right now. How can I help you?`,
			timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
			suggestedPrompts: [
				'Yes, check my PC health',
				'What processes are running?',
				'Is my computer healthy?',
			],
		},
	]);

	const [isListening, setIsListening] = useState<boolean>(false);
	const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
	const [isThinking, setIsThinking] = useState<boolean>(false);
	const [windowState, setWindowState] = useState<'normal' | 'minimized' | 'tray_only'>('normal');

	useEffect(() => {
		try {
			localStorage.setItem('syra_history_events', JSON.stringify(historyEvents));
		} catch (e) {
			console.warn('Failed to persist history to localStorage', e);
		}
	}, [historyEvents]);

	const refreshHistory = useCallback(async () => {
		try {
			const backendIncidents = await api.listIncidents(50);
			if (Array.isArray(backendIncidents) && backendIncidents.length > 0) {
				const mapped: AnomalyEvent[] = backendIncidents
					.filter((inc: any) => inc.resolved === true || inc.action_taken)
					.map((inc: any) => ({
						id: String(inc.id || `inc-${Date.now()}`),
						title: `Fix Applied: ${(inc.action_taken || inc.root_cause || 'System Optimization').replace(/_/g, ' ').toUpperCase()}`,
						summary: inc.action_taken ? `Executed action: ${inc.action_taken.replace(/_/g, ' ')}` : `Resolved issue: ${inc.root_cause}`,
						severity: 'medium',
						timestamp: inc.timestamp ? new Date(inc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently',
						resolved: true,
						rootCause: String(inc.root_cause || 'system_slowdown').replace(/_/g, ' '),
						whyItHappened: `Evidence: ${(inc.evidence || []).join(', ') || 'System monitoring telemetry alert.'}`,
						recommendation: inc.action_taken ? `Applied fix: ${inc.action_taken.replace(/_/g, ' ')}` : 'Automated optimization recommended.',
						futureRisk: 'System performance restored and verified.',
						dialogueHistory: [],
					}));

				setHistoryEvents((prev) => {
					// Deduplicate by rootCause so repeating problems don't duplicate cards
					const mapByCause = new Map<string, AnomalyEvent>();
					for (const item of [...mapped, ...prev]) {
						const key = item.rootCause.toLowerCase().trim();
						if (!mapByCause.has(key)) {
							mapByCause.set(key, item);
						}
					}
					return Array.from(mapByCause.values());
				});
			}
		} catch (e) {
			console.warn('Failed to fetch backend history:', e);
		}
	}, []);

	useEffect(() => {
		void refreshHistory();
	}, [refreshHistory]);

	const recordExecutedRemediation = useCallback((params: {
		action: string;
		rootCause: string;
		message?: string;
		resolved?: boolean;
		before?: any;
		after?: any;
	}) => {
		// Only store in history if the problem was actually solved
		if (params.resolved === false) {
			return;
		}

		const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		const actionClean = params.action.replace(/_/g, ' ');
		const causeClean = params.rootCause.replace(/_/g, ' ');

		const newEvent: AnomalyEvent = {
			id: `rem-${Date.now()}`,
			title: `Fix Applied: ${actionClean.toUpperCase()}`,
			summary: params.message || `Successfully executed ${actionClean} to resolve ${causeClean}.`,
			severity: 'medium',
			timestamp: `Today · ${timeStr}`,
			resolved: true,
			rootCause: causeClean,
			whyItHappened: `Diagnosed ${causeClean} during system monitoring.`,
			recommendation: `Action "${actionClean}" was approved and executed successfully.`,
			futureRisk: 'System performance restored and verified.',
			dialogueHistory: [],
		};

		setHistoryEvents((prev) => {
			// De-duplicate: If the same problem occurred again, update its timestamp rather than duplicate card
			const filtered = prev.filter(e => e.rootCause.toLowerCase().trim() !== causeClean.toLowerCase().trim());
			return [newEvent, ...filtered];
		});
	}, []);

	const updateSettings = useCallback((newSettings: Partial<SystemSettings>) => {
		setSettings((prev) => ({
			...prev,
			...newSettings,
			general: { ...prev.general, ...newSettings.general },
			voice: { ...prev.voice, ...newSettings.voice },
			assistant: { ...prev.assistant, ...newSettings.assistant },
			notifications: { ...prev.notifications, ...newSettings.notifications },
			privacy: { ...prev.privacy, ...newSettings.privacy },
		}));
	}, []);

	// Text-to-speech engine wrapper
	const speakText = useCallback((textToSpeak: string) => {
		if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
			window.speechSynthesis.cancel();
			const cleanText = textToSpeak.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
			const utterance = new SpeechSynthesisUtterance(cleanText);
			utterance.rate = settings.voice.speed;
			utterance.volume = settings.voice.volume;

			utterance.onstart = () => {
				setIsSpeaking(true);
				setAvatarState('speaking');
			};
			utterance.onend = () => {
				setIsSpeaking(false);
				setAvatarState('idle');
			};
			utterance.onerror = () => {
				setIsSpeaking(false);
				setAvatarState('idle');
			};

			window.speechSynthesis.speak(utterance);
		} else {
			// Simulated speech duration
			setIsSpeaking(true);
			setAvatarState('speaking');
			setTimeout(() => {
				setIsSpeaking(false);
				setAvatarState('idle');
			}, Math.min(6000, Math.max(2000, textToSpeak.length * 50)));
		}
	}, [settings.voice.speed, settings.voice.volume]);

	const recognitionRef = React.useRef<any>(null);

	// Auto greeting on app launch
	useEffect(() => {
		const greetingText = `Hello John, I'm SYRA, your computer health monitor. Everything looks healthy right now. How can I help you?`;
		const timer = setTimeout(() => {
			speakText(greetingText);
		}, 600);
		return () => clearTimeout(timer);
	}, [speakText]);

	const stopSpeaking = useCallback(() => {
		if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
			window.speechSynthesis.cancel();
		}
		setIsSpeaking(false);
		setAvatarState('idle');
	}, []);

	const stopListening = useCallback(() => {
		if (recognitionRef.current) {
			try {
				recognitionRef.current.stop();
			} catch {
				// ignore
			}
			recognitionRef.current = null;
		}
		setIsListening(false);
		setAvatarState('idle');
	}, []);

	// Speech Recognition engine wrapper
	const startListening = useCallback(async () => {
		stopSpeaking();

		// Explicitly request microphone permission from the browser if supported
		if (typeof navigator !== 'undefined' && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
			try {
				const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
				// Clean up track immediately so SpeechRecognition can access the microphone cleanly
				stream.getTracks().forEach((track) => track.stop());
			} catch (err) {
				console.warn('Microphone permission request failed or denied:', err);
			}
		}

		if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
			const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

			if (recognitionRef.current) {
				try {
					recognitionRef.current.abort();
				} catch {
					// ignore
				}
			}

			const recognition = new SpeechRecognition();
			recognitionRef.current = recognition;
			recognition.continuous = false;
			recognition.interimResults = true;
			recognition.lang = 'en-US';

			setIsListening(true);
			setAvatarState('listening');

			let capturedText = '';

			recognition.onresult = (event: any) => {
				let transcript = '';
				for (let i = event.resultIndex; i < event.results.length; i++) {
					transcript += event.results[i][0].transcript;
				}
				if (transcript.trim()) {
					capturedText = transcript.trim();
				}

				if (event.results[0]?.isFinal && capturedText) {
					setIsListening(false);
					sendMessage(capturedText);
				}
			};

			recognition.onerror = (event: any) => {
				console.warn('Speech recognition error:', event.error);
				setIsListening(false);
				setAvatarState('idle');
			};

			recognition.onend = () => {
				setIsListening(false);
				if (capturedText && !isThinking) {
					sendMessage(capturedText);
				} else {
					setAvatarState('idle');
				}
			};

			try {
				recognition.start();
			} catch (err) {
				console.warn('Recognition start error:', err);
				setIsListening(false);
				setAvatarState('idle');
			}
		} else {
			setIsListening(true);
			setAvatarState('listening');
			setTimeout(() => {
				setIsListening(false);
				setAvatarState('idle');
				alert('Web Speech API is not supported in this browser environment. Please type your message in the chat or use Chrome/Edge.');
			}, 1500);
		}
	}, [stopSpeaking]);

	// Simulation for background anomaly trigger
	const triggerAnomalySimulation = useCallback(() => {
		const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		const anomaly: AnomalyEvent = {
			id: `anomaly-${Date.now()}`,
			title: 'Live monitoring alert',
			summary: 'A new system alert was detected during the live session.',
			severity: 'medium',
			timestamp: `Today · ${timeStr}`,
			resolved: false,
			rootCause: 'The current monitoring session detected a potential issue.',
			whyItHappened: 'Live monitoring is active and reported a new event.',
			recommendation: 'Continue the conversation with SYRA for guidance.',
			futureRisk: 'Monitoring remains active.',
			dialogueHistory: [],
		};
		setActiveAnomaly(anomaly);
		setNotificationAnomaly(anomaly);
		setShowNotification(true);
		setAvatarState('alert');
	}, []);

	const dismissNotification = useCallback(() => {
		setShowNotification(false);
	}, []);

	const openAnomalyFromNotification = useCallback(() => {
		setShowNotification(false);
		setWindowState('normal');
		if (notificationAnomaly) {
			setActiveAnomaly(notificationAnomaly);
			setActivePage('voice');

			// Setup voice anomaly conversation flow as specified in prompt
			const initialAnomalyMessages: Message[] = [
				{
					id: `anom-start-${Date.now()}`,
					sender: 'syra',
					text: `Hello ${settings.assistant.userName} 👋\nI detected an issue while monitoring your computer.\nWould you like me to explain it?`,
					timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
					suggestedPrompts: ['Yes, explain it', 'Why did this happen?', 'What should I do?'],
				},
			];
			setMessages(initialAnomalyMessages);
			speakText(`Hello ${settings.assistant.userName}. I detected an issue while monitoring your computer. Would you like me to explain it?`);
		}
	}, [notificationAnomaly, settings.assistant.userName, speakText]);

	const resolveActiveAnomaly = useCallback(() => {
		if (activeAnomaly) {
			const resolvedEvent = { ...activeAnomaly, resolved: true };
			setHistoryEvents((prev) => [resolvedEvent, ...prev.filter((e) => e.id !== activeAnomaly.id)]);
			setActiveAnomaly(null);
		}
	}, [activeAnomaly]);

	// Natural Conversation Logic with Anomaly awareness
	const sendMessage = useCallback((userText: string) => {
		const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		const userMsg: Message = {
			id: `user-${Date.now()}`,
			sender: 'user',
			text: userText,
			timestamp: timeStr,
		};

		setMessages((prev) => [...prev, userMsg]);
		setIsThinking(true);
		setAvatarState('thinking');

		// Generate smart natural responses based on conversation state
		setTimeout(async () => {
			setIsThinking(false);

			try {
				const response = await api.sendChatMessage(userText, chatSessionId);
				chatSessionId = response.session_id;
				const syraMsg: Message = {
					id: `syra-${Date.now()}`,
					sender: 'syra',
					text: response.reply,
					timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
				};
				const updatedMessages = [...messages, userMsg, syraMsg];
				setMessages(updatedMessages);
				const conversationId = activeAnomaly ? activeAnomaly.id : `conv-${new Date().toDateString().replace(/\s+/g, '-')}`;
				setHistoryEvents((previous) => [{
					id: conversationId,
					title: activeAnomaly?.title || `SYRA Session: ${userText.slice(0, 25)}${userText.length > 25 ? '...' : ''}`,
					summary: activeAnomaly?.summary || `User query: "${userText}"`,
					severity: activeAnomaly?.severity || 'low',
					timestamp: `Today · ${timeStr}`,
					resolved: !activeAnomaly,
					rootCause: activeAnomaly?.rootCause || (response.used_diagnosis ? 'See SYRA response for the current diagnosis.' : 'No diagnosis available.'),
					whyItHappened: activeAnomaly?.whyItHappened || 'Live backend conversation.',
					recommendation: activeAnomaly?.recommendation || response.reply,
					futureRisk: activeAnomaly?.futureRisk || 'Backend monitoring remains active.',
					dialogueHistory: updatedMessages,
				}, ...previous.filter((event) => event.id !== conversationId)]);
				if (settings.voice.autoSpeakResponse) {
					speakText(response.reply);
				} else {
					setAvatarState('idle');
				}
				return;
			} catch (error) {
				console.warn('SYRA backend is unavailable; using the local response fallback.', error);
			}

			const lower = userText.toLowerCase();
			let responseText = '';
			let prompts: string[] | undefined = undefined;

			if (activeAnomaly) {
				if (lower.includes('yes') || lower.includes('explain') || lower.includes('sure') || lower.includes('tell me')) {
					responseText = `I found the likely cause. The issue appears to be related to excessive memory usage by Chrome.`;
					prompts = ['Why did this happen?', 'What should I do?'];
				} else if (lower.includes('why') || lower.includes('cause') || lower.includes('happen')) {
					responseText = `Your memory usage increased gradually, and Chrome was using a large amount of RAM at the same time. That combination caused increasing memory pressure on your computer.`;
					prompts = ['What should I do?', 'Can this happen again?'];
				} else if (lower.includes('what should i do') || lower.includes('fix') || lower.includes('recommend') || lower.includes('action')) {
					responseText = `I recommend closing some unused Chrome tabs first. If the problem continues, restarting Chrome should reduce the memory pressure.`;
					prompts = ['Can this happen again?', 'Resolve this issue'];
				} else if (lower.includes('again') || lower.includes('future') || lower.includes('recur') || lower.includes('prevent')) {
					responseText = `It could happen again if Chrome continues to consume a large amount of memory. I'll continue monitoring your computer and let you know if I notice the same pattern developing.`;
					prompts = ['Resolve this issue', 'Thank you SYRA'];
				} else if (lower.includes('resolve') || lower.includes('done') || lower.includes('fixed') || lower.includes('close') || lower.includes('thank')) {
					resolveActiveAnomaly();
					responseText = `Glad I could help, ${settings.assistant.userName}. I've logged this to your History and resumed silent background monitoring. Everything looks healthy now!`;
					prompts = ['Is my computer healthy?', 'Check background tasks'];
				} else {
					responseText = `I'm tracking the Chrome memory pressure anomaly. I can explain why it happened, recommend actions, or predict future risks for you.`;
					prompts = ['Why did this happen?', 'What should I do?', 'Can this happen again?'];
				}
			} else {
				// Normal conversational responses
				if (lower.includes('yes') || lower.includes('sure') || lower.includes('okay') || lower.includes('check') || lower.includes('pc') || lower.includes('health')) {
					responseText = `Great! I ran a live telemetry check. CPU load is low at 18%, memory is steady at 4.2GB, and 84 background processes are running normally without any anomalies.`;
					prompts = ['Check background tasks', 'Simulate Anomaly', 'What do you monitor?'];
				} else if (lower.includes('hello') || lower.includes('hi') || lower.includes('hey')) {
					responseText = `Hello John 👋\nEverything looks healthy right now. How can I help you today?`;
					prompts = ['Yes, check my PC health', 'Check background tasks'];
				} else if (lower.includes('task') || lower.includes('process') || lower.includes('background')) {
					responseText = `I'm quietly supervising 84 active system processes. All core Windows/macOS services are operating within normal parameters without memory leaks.`;
					prompts = ['Simulate Anomaly', 'How do you monitor?'];
				} else if (lower.includes('simulate') || lower.includes('test') || lower.includes('anomaly')) {
					triggerAnomalySimulation();
					responseText = `I've triggered a background anomaly simulation. Check the desktop notification alert at the bottom-left of your screen!`;
				} else {
					responseText = `As your computer health assistant, I'm continuously monitoring system metrics in the background. Everything is running smoothly! Feel free to ask me any question about your system.`;
					prompts = ['Yes, check my PC health', 'Simulate Anomaly'];
				}
			}

			const syraMsg: Message = {
				id: `syra-${Date.now()}`,
				sender: 'syra',
				text: responseText,
				timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
				suggestedPrompts: prompts,
			};

			const updatedMessages = [...messages, userMsg, syraMsg];
			setMessages(updatedMessages);

			// Automatically store conversation into historyEvents whenever the user talks with SYRA
			const conversationId = activeAnomaly ? activeAnomaly.id : `conv-${new Date().toDateString().replace(/\s+/g, '-')}`;
			const eventTitle = activeAnomaly
				? activeAnomaly.title
				: `Voice Session: ${userText.length > 25 ? userText.slice(0, 25) + '...' : userText}`;

			const updatedEvent: AnomalyEvent = {
				id: conversationId,
				title: eventTitle,
				summary: activeAnomaly ? activeAnomaly.summary : `User voice dialogue: "${userText}"`,
				severity: activeAnomaly ? activeAnomaly.severity : 'low',
				timestamp: `Today · ${timeStr}`,
				resolved: activeAnomaly ? activeAnomaly.resolved : true,
				rootCause: activeAnomaly ? activeAnomaly.rootCause : 'User initiated computer health voice interaction.',
				whyItHappened: activeAnomaly ? activeAnomaly.whyItHappened : 'Routine user system query and voice telemetry check.',
				recommendation: activeAnomaly ? activeAnomaly.recommendation : 'SYRA answered question and confirmed background telemetry status.',
				futureRisk: activeAnomaly ? activeAnomaly.futureRisk : 'None. System metrics operating within healthy parameters.',
				dialogueHistory: updatedMessages,
			};

			setHistoryEvents((prev) => {
				const index = prev.findIndex((e) => e.id === conversationId);
				if (index >= 0) {
					const newArr = [...prev];
					newArr[index] = updatedEvent;
					return newArr;
				} else {
					return [updatedEvent, ...prev];
				}
			});

			if (settings.voice.autoSpeakResponse) {
				speakText(responseText);
			} else {
				setAvatarState('idle');
			}
		}, 800);
	}, [activeAnomaly, messages, resolveActiveAnomaly, settings.assistant.userName, settings.voice.autoSpeakResponse, speakText, triggerAnomalySimulation]);

	const clearMessages = useCallback(() => {
		setMessages([]);
	}, []);

	const healthState: SystemHealthState = {
		status: activeAnomaly ? 'anomaly_detected' : 'healthy',
		activeAnomaly,
		lastScanTime: 'Just now',
		backgroundMonitoringActive: settings.general.backgroundMonitoring,
	};

	return (
		<SYRAContext.Provider
			value={{
				activePage,
				setActivePage,
				avatarState,
				setAvatarState,
				settings,
				updateSettings,
				healthState,
				showNotification,
				notificationAnomaly,
				triggerAnomalySimulation,
				dismissNotification,
				openAnomalyFromNotification,
				messages,
				sendMessage,
				clearMessages,
				historyEvents,
				selectedHistoryEvent,
				setSelectedHistoryEvent,
				isListening,
				isSpeaking,
				isThinking,
				startListening,
				stopListening,
				speakText,
				stopSpeaking,
				windowState,
				setWindowState,
				resolveActiveAnomaly,
				recordExecutedRemediation,
				refreshHistory,
			}}
		>
			{children}
		</SYRAContext.Provider>
	);
};

export const useSYRA = () => {
	const context = useContext(SYRAContext);
	if (!context) {
		throw new Error('useSYRA must be used within a SYRAProvider');
	}
	return context;
};
