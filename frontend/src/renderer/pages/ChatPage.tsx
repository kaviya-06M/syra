import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import { MessageSquare, Sparkles, Send, Bot, User, RefreshCw, Terminal, ShieldAlert } from 'lucide-react';

type ChatRole = 'user' | 'assistant';

type ChatMessage = {
	role: ChatRole;
	content: string;
};

type ChatResponse = {
	session_id: string;
	reply: string;
	used_diagnosis?: boolean;
	llm_ready?: boolean;
	llm_error?: string | null;
};

type DiagnosisResponse = {
	root_cause?: string | null;
	confidence?: number;
	evidence?: string[];
	timestamp?: string;
	message?: string;
};

interface ChatPageProps {
	diagnosis: DiagnosisResponse | null;
}

const STORAGE_KEY = 'syra.chat.sessionId';

function getInitialSessionId() {
	try {
		const stored = window.localStorage.getItem(STORAGE_KEY);
		return stored || `session-${Date.now()}`;
	} catch {
		return `session-${Date.now()}`;
	}
}

async function sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
	const response = await fetch('/api/chat/message', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ message, session_id: sessionId }),
	});

	if (!response.ok) {
		const text = await response.text();
		throw new Error(text || `Request failed with status ${response.status}`);
	}

	return response.json();
}

export default function ChatPage({ diagnosis }: ChatPageProps) {
	const [sessionId, setSessionId] = useState('');
	const [input, setInput] = useState('');
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [isSending, setIsSending] = useState(false);
	const [error, setError] = useState('');

	useEffect(() => {
		const nextSessionId = getInitialSessionId();
		setSessionId(nextSessionId);
		try {
			window.localStorage.setItem(STORAGE_KEY, nextSessionId);
		} catch {
			// Ignore storage errors.
		}
	}, []);

	useEffect(() => {
		if (diagnosis?.root_cause && messages.length === 0) {
			const confidenceText = typeof diagnosis.confidence === 'number'
				? `Confidence: ${Math.round(diagnosis.confidence * 100)}%.`
				: '';
			const evidenceText = diagnosis.evidence && diagnosis.evidence.length > 0
				? `Evidence: ${diagnosis.evidence.slice(0, 3).join(', ')}.`
				: '';

			setMessages([
				{
					role: 'assistant',
					content: `Root cause: ${diagnosis.root_cause}. ${confidenceText} ${evidenceText}`,
				},
			]);
		}
	}, [diagnosis]);

	const canSend = useMemo(() => input.trim().length > 0 && !isSending, [input, isSending]);

	async function handleSubmit(textToSend?: string) {
		const targetText = (textToSend || input).trim();
		if (!targetText || isSending) {
			return;
		}

		const userMessage: ChatMessage = { role: 'user', content: targetText };
		setMessages((current) => [...current, userMessage]);
		setInput('');
		setIsSending(true);
		setError('');

		try {
			const response = await sendChatMessage(targetText, sessionId);
			try {
				window.localStorage.setItem(STORAGE_KEY, response.session_id);
			} catch {
				// Ignore storage errors.
			}
			setSessionId(response.session_id);
			setMessages((current) => [
				...current,
				{
					role: 'assistant',
					content: response.reply,
				},
			]);
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to send chat message.';
			setError(message);
		} finally {
			setIsSending(false);
		}
	}

	function handleFormSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		void handleSubmit();
	}

	const promptSuggestions = [
		'Analyze CPU utilization and top processes',
		'Check memory pressure and potential leaks',
		'Is my computer operating within normal thresholds?',
		'What remediation actions are recommended?',
	];

	return (
		<div style={styles.container}>
			{/* Header Banner */}
			<section style={styles.heroCard}>
				<div style={styles.heroLeft}>
					<div style={styles.iconBox}>
						<Bot size={24} color="#38bdf8" />
					</div>
					<div>
						<div style={styles.kicker}>SYRA INTELLIGENT COMPANION</div>
						<h1 style={styles.title}>AI Computer Health Assistant</h1>
						<p style={styles.description}>
							Ask SYRA natural language questions about telemetry anomalies, hardware pressure, and process optimization.
						</p>
					</div>
				</div>
			</section>

			{/* Chat Area */}
			<section style={styles.chatCard}>
				{/* Diagnosis Context Bar */}
				{diagnosis?.root_cause && (
					<div style={styles.diagnosisBar}>
						<ShieldAlert size={16} color="#7dd3fc" />
						<div style={styles.diagnosisText}>
							<strong>Live Diagnosis Context:</strong> {diagnosis.root_cause}
						</div>
					</div>
				)}

				<div style={styles.chatLog}>
					{messages.length === 0 ? (
						<div style={styles.emptyState}>
							<Bot size={40} color="#38bdf8" style={{ marginBottom: '12px' }} />
							<div style={styles.emptyTitle}>How can SYRA assist your computer today?</div>
							<div style={styles.emptyText}>
								Select a quick prompt below or type your question in the message box.
							</div>

							<div style={styles.promptGrid}>
								{promptSuggestions.map((prompt, idx) => (
									<button
										key={idx}
										type="button"
										onClick={() => void handleSubmit(prompt)}
										style={styles.promptChip}
									>
										<Sparkles size={14} color="#38bdf8" />
										<span>{prompt}</span>
									</button>
								))}
							</div>
						</div>
					) : (
						messages.map((message, index) => (
							<div
								key={`${message.role}-${index}`}
								style={message.role === 'user' ? styles.userBubble : styles.assistantBubble}
							>
								<div style={styles.bubbleHeader}>
									{message.role === 'user' ? <User size={14} color="#93c5fd" /> : <Bot size={14} color="#38bdf8" />}
									<span style={styles.bubbleLabel}>{message.role === 'user' ? 'You' : 'SYRA AI'}</span>
								</div>
								<div style={styles.bubbleText}>{message.content}</div>
							</div>
						))
					)}

					{isSending && (
						<div style={styles.assistantBubble}>
							<div style={styles.bubbleHeader}>
								<Bot size={14} color="#38bdf8" />
								<span style={styles.bubbleLabel}>SYRA AI</span>
							</div>
							<div style={styles.bubbleText}>Analyzing system metrics...</div>
						</div>
					)}
				</div>

				<form onSubmit={handleFormSubmit} style={styles.form}>
					{error ? <div style={styles.errorBox}>{error}</div> : null}

					<div style={styles.inputWrapper}>
						<textarea
							value={input}
							onChange={(e) => setInput(e.target.value)}
							onKeyDown={(e) => {
								if (e.key === 'Enter' && !e.shiftKey) {
									e.preventDefault();
									void handleSubmit();
								}
							}}
							placeholder="Ask SYRA about CPU, RAM, disk, or computer health..."
							rows={2}
							style={styles.textarea}
						/>
						<button type="submit" disabled={!canSend} style={canSend ? styles.sendBtn : styles.sendBtnDisabled}>
							<Send size={16} />
							<span>{isSending ? 'Sending' : 'Send'}</span>
						</button>
					</div>
				</form>
			</section>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'grid',
		gap: '20px',
	},
	heroCard: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(10, 20, 38, 0.85)',
		border: '1px solid rgba(56, 189, 248, 0.18)',
		boxShadow: '0 20px 50px rgba(0, 0, 0, 0.35)',
		backdropFilter: 'blur(16px)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '20px',
	},
	heroLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
	},
	iconBox: {
		width: '50px',
		height: '50px',
		borderRadius: '14px',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	kicker: {
		fontSize: '11px',
		letterSpacing: '0.12em',
		color: '#38bdf8',
		fontWeight: 700,
	},
	title: {
		margin: '4px 0',
		fontSize: '22px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	description: {
		margin: 0,
		fontSize: '13px',
		color: '#94a3b8',
	},
	chatCard: {
		padding: '20px',
		borderRadius: '24px',
		background: 'rgba(15, 23, 42, 0.82)',
		border: '1px solid rgba(148, 163, 184, 0.15)',
		display: 'grid',
		gap: '16px',
	},
	diagnosisBar: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		padding: '12px 16px',
		borderRadius: '14px',
		background: 'rgba(15, 23, 42, 0.9)',
		border: '1px solid rgba(125, 211, 252, 0.2)',
	},
	diagnosisText: {
		fontSize: '13px',
		color: '#e2e8f0',
	},
	chatLog: {
		minHeight: '340px',
		maxHeight: '52vh',
		overflowY: 'auto',
		display: 'flex',
		flexDirection: 'column',
		gap: '14px',
		padding: '4px',
	},
	emptyState: {
		padding: '40px 20px',
		textAlign: 'center',
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		justifyContent: 'center',
	},
	emptyTitle: {
		fontSize: '18px',
		fontWeight: 700,
		color: '#f8fafc',
		marginBottom: '6px',
	},
	emptyText: {
		fontSize: '13px',
		color: '#94a3b8',
		marginBottom: '24px',
	},
	promptGrid: {
		display: 'grid',
		gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
		gap: '10px',
		width: '100%',
		maxWidth: '720px',
	},
	promptChip: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
		padding: '12px 16px',
		borderRadius: '14px',
		background: 'rgba(30, 41, 59, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.12)',
		color: '#cbd5e1',
		fontSize: '12px',
		fontWeight: 500,
		cursor: 'pointer',
		textAlign: 'left',
		transition: 'all 0.2s ease',
	},
	userBubble: {
		alignSelf: 'flex-end',
		maxWidth: '85%',
		padding: '14px 18px',
		borderRadius: '18px 18px 4px 18px',
		background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.9), rgba(15, 118, 110, 0.9))',
		color: '#f8fafc',
		boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
	},
	assistantBubble: {
		alignSelf: 'flex-start',
		maxWidth: '85%',
		padding: '14px 18px',
		borderRadius: '18px 18px 18px 4px',
		background: 'rgba(30, 41, 59, 0.9)',
		border: '1px solid rgba(148, 163, 184, 0.15)',
		color: '#e2e8f0',
	},
	bubbleHeader: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		marginBottom: '6px',
	},
	bubbleLabel: {
		fontSize: '11px',
		fontWeight: 700,
		letterSpacing: '0.05em',
		textTransform: 'uppercase',
		color: '#94a3b8',
	},
	bubbleText: {
		fontSize: '14px',
		lineHeight: 1.6,
		whiteSpace: 'pre-wrap',
	},
	form: {
		display: 'grid',
		gap: '10px',
	},
	inputWrapper: {
		display: 'flex',
		gap: '12px',
		alignItems: 'flex-end',
	},
	textarea: {
		flex: 1,
		padding: '14px 16px',
		borderRadius: '16px',
		background: 'rgba(10, 20, 38, 0.9)',
		border: '1px solid rgba(148, 163, 184, 0.2)',
		color: '#f8fafc',
		fontSize: '14px',
		outline: 'none',
		resize: 'none',
		fontFamily: 'inherit',
	},
	sendBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '14px 22px',
		borderRadius: '16px',
		border: 'none',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		color: '#fff',
		fontWeight: 700,
		fontSize: '13px',
		cursor: 'pointer',
		boxShadow: '0 8px 20px rgba(37, 99, 235, 0.35)',
	},
	sendBtnDisabled: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '14px 22px',
		borderRadius: '16px',
		border: 'none',
		background: 'rgba(71, 85, 105, 0.4)',
		color: '#64748b',
		fontWeight: 700,
		fontSize: '13px',
		cursor: 'not-allowed',
	},
	errorBox: {
		padding: '10px 14px',
		borderRadius: '12px',
		background: 'rgba(127, 29, 29, 0.4)',
		border: '1px solid rgba(248, 113, 113, 0.3)',
		color: '#fecaca',
		fontSize: '13px',
	},
};
