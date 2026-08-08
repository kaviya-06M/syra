import React, { FormEvent, useEffect, useMemo, useState } from 'react';

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

const STORAGE_KEY = 'syra.chat.sessionId';
const DEFAULT_API_BASE = 'http://127.0.0.1:8000';

function getInitialSessionId() {
	try {
		const stored = window.localStorage.getItem(STORAGE_KEY);
		return stored || `session-${Date.now()}`;
	} catch {
		return `session-${Date.now()}`;
	}
}

async function sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
	const response = await fetch(`${DEFAULT_API_BASE}/api/chat/message`, {
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

async function fetchLatestDiagnosis(): Promise<DiagnosisResponse> {
	const response = await fetch(`${DEFAULT_API_BASE}/api/diagnosis/latest`);

	if (!response.ok) {
		const text = await response.text();
		throw new Error(text || `Request failed with status ${response.status}`);
	}

	return response.json();
}

export default function ChatPage() {
	const [sessionId, setSessionId] = useState('');
	const [input, setInput] = useState('');
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [isSending, setIsSending] = useState(false);
	const [error, setError] = useState('');
	const [diagnosisSummary, setDiagnosisSummary] = useState('Loading latest diagnosis...');
	const [diagnosisState, setDiagnosisState] = useState<'loading' | 'ready' | 'empty' | 'error'>('loading');

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
		let active = true;

		async function loadDiagnosis() {
			try {
				const latest = await fetchLatestDiagnosis();
				if (!active) {
					return;
				}

				if (latest.root_cause) {
					const confidenceText = typeof latest.confidence === 'number' ? `Confidence: ${Math.round(latest.confidence * 1000) / 10}%.` : 'Confidence: unknown.';
					const evidenceText = latest.evidence && latest.evidence.length > 0 ? `Evidence: ${latest.evidence.slice(0, 3).join(', ')}.` : 'Evidence: none provided.';
					setDiagnosisSummary(`Root cause: ${latest.root_cause}. ${confidenceText} ${evidenceText}`);
					setDiagnosisState('ready');
					setMessages([
						{
							role: 'assistant',
							content: `Root cause: ${latest.root_cause}. ${confidenceText} ${evidenceText}`,
						},
					]);
				} else {
					setDiagnosisSummary('No diagnosis has been run yet. Ask SYRA a question to analyze the latest telemetry.');
					setDiagnosisState('empty');
				}
			} catch (loadError) {
				if (!active) {
					return;
				}

				const message = loadError instanceof Error ? loadError.message : 'Failed to load diagnosis.';
				setDiagnosisSummary(message);
				setDiagnosisState('error');
			}
		}

		void loadDiagnosis();

		return () => {
			active = false;
		};
	}, []);

	const canSend = useMemo(() => input.trim().length > 0 && !isSending, [input, isSending]);

	async function handleSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const trimmed = input.trim();
		if (!trimmed || isSending) {
			return;
		}

		const userMessage: ChatMessage = { role: 'user', content: trimmed };
		setMessages((current) => [...current, userMessage]);
		setInput('');
		setIsSending(true);
		setError('');

		try {
			const response = await sendChatMessage(trimmed, sessionId);
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

	return (
		<div style={styles.page}>
			<div style={styles.glowOne} />
			<div style={styles.glowTwo} />

			<main style={styles.shell}>
				<section style={styles.headerCard}>
					<div>
						<div style={styles.kicker}>SYRA Chat</div>
						<h1 style={styles.title}>SYRA is an AI Computer Health Monitor</h1>
						<p style={styles.subtitle}>
							Ask SYRA about your computer health. This page sends your question to <strong>/api/chat/message</strong> and shows the reply returned by the LLM pipeline.
						</p>
					</div>
				</section>

				<section style={styles.chatCard}>
					<div style={styles.diagnosisCard}>
						<div style={styles.diagnosisLabel}>Latest Diagnosis</div>
						<div style={styles.diagnosisText}>{diagnosisSummary}</div>
					</div>

					<div style={styles.responseLabel}>SYRA Response</div>
					<div style={styles.chatLog}>
						{messages.length === 0 ? (
							<div style={styles.emptyState}>
								<div style={styles.emptyTitle}>No messages yet</div>
								<div style={styles.emptyText}>
									Ask about your computer health.
								</div>
							</div>
						) : (
							messages.map((message, index) => (
								<div
									key={`${message.role}-${index}`}
									style={message.role === 'user' ? styles.userBubble : styles.assistantBubble}
								>
									<div style={styles.bubbleLabel}>{message.role === 'user' ? 'You' : 'SYRA'}</div>
									<div style={styles.bubbleText}>{message.content}</div>
								</div>
							))
						)}

						{isSending ? (
							<div style={styles.assistantBubble}>
								<div style={styles.bubbleLabel}>SYRA</div>
								<div style={styles.bubbleText}>Thinking...</div>
							</div>
						) : null}
					</div>

					<form onSubmit={handleSubmit} style={styles.form}>
						<label style={styles.label} htmlFor="chat-input">
							Ask about your computer health
						</label>
						<textarea
							id="chat-input"
							value={input}
							onChange={(event) => setInput(event.target.value)}
							placeholder='Ask about your computer health'
							rows={4}
							style={styles.textarea}
						/>

						{error ? <div style={styles.errorBox}>{error}</div> : null}

						<div style={styles.actionsRow}>
							<div style={styles.helperText}>The reply is read from the backend JSON `reply` field.</div>
							<button type="submit" disabled={!canSend} style={canSend ? styles.button : styles.buttonDisabled}>
								{isSending ? 'Sending...' : 'Send'}
							</button>
						</div>
					</form>
				</section>
			</main>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	page: {
		minHeight: '100vh',
		padding: '32px 20px',
		background:
			'radial-gradient(circle at top left, rgba(251, 146, 60, 0.18), transparent 32%), radial-gradient(circle at top right, rgba(34, 197, 94, 0.16), transparent 28%), linear-gradient(180deg, #07111f 0%, #0a1627 48%, #0d1320 100%)',
		color: '#eef4ff',
		position: 'relative',
		overflow: 'hidden',
		fontFamily: '"Segoe UI", "Inter", system-ui, sans-serif',
	},
	shell: {
		width: 'min(980px, 100%)',
		margin: '0 auto',
		position: 'relative',
		zIndex: 1,
		display: 'grid',
		gap: '20px',
	},
	headerCard: {
		display: 'flex',
		justifyContent: 'space-between',
		gap: '16px',
		padding: '24px',
		borderRadius: '24px',
		background: 'rgba(8, 15, 28, 0.78)',
		border: '1px solid rgba(148, 163, 184, 0.16)',
		boxShadow: '0 24px 70px rgba(0, 0, 0, 0.36)',
		backdropFilter: 'blur(16px)',
		flexWrap: 'wrap',
	},
	kicker: {
		textTransform: 'uppercase',
		letterSpacing: '0.22em',
		fontSize: '12px',
		color: '#7dd3fc',
		marginBottom: '10px',
	},
	title: {
		margin: 0,
		fontSize: 'clamp(28px, 4vw, 46px)',
		lineHeight: 1.05,
	},
	subtitle: {
		margin: '12px 0 0',
		maxWidth: '62ch',
		color: '#aab7cf',
		lineHeight: 1.6,
	},
	chatCard: {
		padding: '20px',
		borderRadius: '28px',
		background: 'rgba(8, 15, 28, 0.78)',
		border: '1px solid rgba(148, 163, 184, 0.16)',
		boxShadow: '0 24px 70px rgba(0, 0, 0, 0.36)',
		backdropFilter: 'blur(16px)',
		display: 'grid',
		gap: '18px',
	},
	diagnosisCard: {
		padding: '16px 18px',
		borderRadius: '20px',
		background: 'rgba(15, 23, 42, 0.84)',
		border: '1px solid rgba(125, 211, 252, 0.18)',
		display: 'grid',
		gap: '8px',
	},
	diagnosisLabel: {
		textTransform: 'uppercase',
		letterSpacing: '0.14em',
		fontSize: '12px',
		color: '#7dd3fc',
	},
	diagnosisText: {
		color: '#e2e8f0',
		lineHeight: 1.6,
	},
	responseLabel: {
		textTransform: 'uppercase',
		letterSpacing: '0.14em',
		fontSize: '12px',
		color: '#7dd3fc',
	},
	chatLog: {
		minHeight: '320px',
		maxHeight: '56vh',
		overflowY: 'auto',
		display: 'grid',
		gap: '14px',
		padding: '6px',
	},
	emptyState: {
		minHeight: '260px',
		display: 'grid',
		placeItems: 'center',
		textAlign: 'center',
		borderRadius: '22px',
		border: '1px dashed rgba(148, 163, 184, 0.22)',
		background: 'rgba(15, 23, 42, 0.46)',
		color: '#cbd5e1',
		padding: '24px',
	},
	emptyTitle: {
		fontSize: '18px',
		fontWeight: 700,
		marginBottom: '8px',
	},
	emptyText: {
		color: '#94a3b8',
	},
	codeText: {
		color: '#7dd3fc',
		fontWeight: 600,
	},
	userBubble: {
		justifySelf: 'end',
		width: 'min(720px, 90%)',
		padding: '16px 18px',
		borderRadius: '20px 20px 6px 20px',
		background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.88), rgba(15, 118, 110, 0.88))',
		color: '#f8fbff',
		boxShadow: '0 16px 32px rgba(15, 23, 42, 0.28)',
	},
	assistantBubble: {
		justifySelf: 'start',
		width: 'min(720px, 90%)',
		padding: '16px 18px',
		borderRadius: '20px 20px 20px 6px',
		background: 'rgba(15, 23, 42, 0.95)',
		border: '1px solid rgba(148, 163, 184, 0.16)',
		color: '#e2e8f0',
	},
	bubbleLabel: {
		fontSize: '12px',
		textTransform: 'uppercase',
		letterSpacing: '0.14em',
		color: '#93c5fd',
		marginBottom: '8px',
	},
	bubbleText: {
		whiteSpace: 'pre-wrap',
		lineHeight: 1.65,
	},
	form: {
		display: 'grid',
		gap: '12px',
		paddingTop: '6px',
	},
	label: {
		fontSize: '13px',
		textTransform: 'uppercase',
		letterSpacing: '0.12em',
		color: '#94a3b8',
	},
	textarea: {
		width: '100%',
		resize: 'vertical',
		minHeight: '120px',
		padding: '16px 18px',
		borderRadius: '18px',
		border: '1px solid rgba(148, 163, 184, 0.18)',
		background: 'rgba(15, 23, 42, 0.92)',
		color: '#eef4ff',
		outline: 'none',
		fontSize: '15px',
		lineHeight: 1.5,
		boxSizing: 'border-box',
	},
	errorBox: {
		padding: '12px 14px',
		borderRadius: '14px',
		background: 'rgba(127, 29, 29, 0.42)',
		border: '1px solid rgba(248, 113, 113, 0.22)',
		color: '#fecaca',
	},
	actionsRow: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '12px',
		flexWrap: 'wrap',
	},
	helperText: {
		color: '#94a3b8',
		fontSize: '13px',
	},
	button: {
		border: 'none',
		borderRadius: '999px',
		padding: '12px 22px',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		color: '#fff',
		fontWeight: 700,
		cursor: 'pointer',
		boxShadow: '0 12px 28px rgba(37, 99, 235, 0.35)',
	},
	buttonDisabled: {
		border: 'none',
		borderRadius: '999px',
		padding: '12px 22px',
		background: 'rgba(71, 85, 105, 0.6)',
		color: '#cbd5e1',
		fontWeight: 700,
		cursor: 'not-allowed',
	},
	glowOne: {
		position: 'absolute',
		width: '420px',
		height: '420px',
		borderRadius: '50%',
		background: 'radial-gradient(circle, rgba(56, 189, 248, 0.18), transparent 65%)',
		top: '-140px',
		left: '-120px',
		filter: 'blur(10px)',
	},
	glowTwo: {
		position: 'absolute',
		width: '340px',
		height: '340px',
		borderRadius: '50%',
		background: 'radial-gradient(circle, rgba(251, 191, 36, 0.12), transparent 68%)',
		bottom: '-120px',
		right: '-80px',
		filter: 'blur(8px)',
	},
};
