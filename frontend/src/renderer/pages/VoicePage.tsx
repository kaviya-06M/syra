import React, { useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { Bot, RefreshCw, Trash2, ShieldCheck, ShieldAlert } from 'lucide-react';
import SYRAAvatar from '../../components/SYRAAvatar';
import ChatBubble from '../../components/ChatBubble';
import ChatInput from '../../components/ChatInput';
import ThinkingAnimation from '../../components/ThinkingAnimation';
import { useSYRA } from '../../context/SYRAContext';

export default function VoicePage() {
	const {
		messages,
		sendMessage,
		clearMessages,
		avatarState,
		isListening,
		isSpeaking,
		isThinking,
		startListening,
		stopListening,
		healthState,
		resolveActiveAnomaly,
		selectedHistoryEvent,
		setSelectedHistoryEvent,
	} = useSYRA();

	const chatEndRef = useRef<HTMLDivElement>(null);
	const activeMessages = selectedHistoryEvent && selectedHistoryEvent.dialogueHistory.length > 0 
		? selectedHistoryEvent.dialogueHistory 
		: messages;

	useEffect(() => {
		chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [activeMessages, isThinking]);

	const hasAnomaly = !!healthState.activeAnomaly;

	const handleToggleListening = () => {
		if (isListening) {
			stopListening();
		} else {
			startListening();
		}
	};

	return (
		<div style={styles.container}>
			{/* Top Stage: SYRA AI Orb & Voice State Indicator */}
			<div style={styles.avatarStage}>
				<SYRAAvatar
					state={avatarState}
					size={180}
					onClick={handleToggleListening}
				/>

				<div style={styles.avatarStateLabel}>
					{isListening ? (
						<span style={{ color: '#f43f5e', fontWeight: 700 }}>● Listening...</span>
					) : isSpeaking ? (
						<span style={{ color: '#38bdf8', fontWeight: 700 }}>🔊 Speaking...</span>
					) : isThinking ? (
						<span style={{ color: '#c084fc', fontWeight: 700 }}>⚡ Analyzing system metrics...</span>
					) : hasAnomaly ? (
						<span style={{ color: '#f87171', fontWeight: 700 }}>⚠ Anomaly Detected</span>
					) : (
						<span style={{ color: '#94a3b8' }}>Monitoring your computer...</span>
					)}
				</div>
			</div>

			{/* Middle Stage: Conversation Transcript */}
			<div style={styles.transcriptCard}>
				<div style={styles.transcriptHeader}>
					<div style={styles.transcriptTitleRow}>
						<Bot size={16} color="#38bdf8" />
						<span style={styles.transcriptTitle}>
							{selectedHistoryEvent ? `History Log: ${selectedHistoryEvent.title}` : 'SYRA Live Voice Transcript'}
						</span>
					</div>

					<div style={styles.headerActions}>
						{selectedHistoryEvent ? (
							<button
								type="button"
								onClick={() => setSelectedHistoryEvent(null)}
								style={styles.liveSessionBtn}
							>
								<span>Back to Live Assistant</span>
							</button>
						) : (
							<>
								{hasAnomaly && (
									<button
										type="button"
										onClick={resolveActiveAnomaly}
										style={styles.resolveBtn}
									>
										<ShieldCheck size={12} />
										<span>Resolve Anomaly</span>
									</button>
								)}

								<button
									type="button"
									onClick={clearMessages}
									style={styles.clearBtn}
									title="Clear Transcript"
								>
									<Trash2 size={14} color="#94a3b8" />
								</button>
							</>
						)}
					</div>
				</div>

				<div style={styles.chatLog}>
					{activeMessages.map((msg) => (
						<ChatBubble
							key={msg.id}
							message={msg}
							onPromptClick={(prompt) => {
								if (selectedHistoryEvent) {
									setSelectedHistoryEvent(null);
								}
								sendMessage(prompt);
							}}
						/>
					))}

					{isThinking && <ThinkingAnimation />}

					<div ref={chatEndRef} />
				</div>
			</div>

			{/* Bottom Stage: Voice & Text Input */}
			<div style={styles.inputArea}>
				<ChatInput
					onSendMessage={sendMessage}
					isListening={isListening}
					isSpeaking={isSpeaking}
					onToggleListening={handleToggleListening}
					disabled={isThinking}
				/>
			</div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'grid',
		gap: '20px',
		width: '100%',
		maxWidth: '860px',
		margin: '0 auto',
	},
	pipelineHeaderRow: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'flex-end',
		marginBottom: '-6px',
	},
	flowModeToggle: {
		display: 'flex',
		alignItems: 'center',
		gap: '4px',
		padding: '3px',
		borderRadius: '12px',
		background: 'rgba(15, 23, 42, 0.7)',
		border: '1px solid rgba(148, 163, 184, 0.15)',
	},
	toggleBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		padding: '5px 12px',
		borderRadius: '9px',
		border: 'none',
		background: 'transparent',
		color: '#94a3b8',
		fontSize: '11px',
		fontWeight: 600,
		cursor: 'pointer',
		transition: 'all 0.2s ease',
	},
	toggleBtnActive: {
		background: 'rgba(56, 189, 248, 0.2)',
		color: '#38bdf8',
		fontWeight: 700,
	},
	avatarStage: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		justifyContent: 'center',
		gap: '12px',
		padding: '16px 0 8px',
	},
	avatarStateLabel: {
		fontSize: '13px',
		letterSpacing: '0.05em',
		textTransform: 'uppercase',
		minHeight: '20px',
	},
	transcriptCard: {
		borderRadius: '24px',
		background: 'rgba(10, 15, 28, 0.85)',
		border: '1px solid rgba(56, 189, 248, 0.18)',
		padding: '20px',
		backdropFilter: 'blur(16px)',
		boxShadow: '0 20px 50px rgba(0, 0, 0, 0.35)',
		display: 'flex',
		flexDirection: 'column',
		gap: '16px',
	},
	transcriptHeader: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		paddingBottom: '12px',
		borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
	},
	transcriptTitleRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
	},
	transcriptTitle: {
		fontSize: '13px',
		fontWeight: 700,
		color: '#f8fafc',
		letterSpacing: '0.02em',
	},
	headerActions: {
		display: 'flex',
		alignItems: 'center',
		gap: '10px',
	},
	resolveBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		padding: '4px 10px',
		borderRadius: '10px',
		background: 'rgba(34, 197, 94, 0.15)',
		border: '1px solid rgba(34, 197, 94, 0.3)',
		color: '#4ade80',
		fontSize: '11px',
		fontWeight: 700,
		cursor: 'pointer',
	},
	liveSessionBtn: {
		display: 'flex',
		alignItems: 'center',
		padding: '4px 12px',
		borderRadius: '10px',
		background: 'rgba(56, 189, 248, 0.15)',
		border: '1px solid rgba(56, 189, 248, 0.3)',
		color: '#38bdf8',
		fontSize: '11px',
		fontWeight: 700,
		cursor: 'pointer',
	},
	clearBtn: {
		background: 'transparent',
		border: 'none',
		cursor: 'pointer',
		padding: '4px',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
	},
	chatLog: {
		display: 'flex',
		flexDirection: 'column',
		gap: '14px',
		maxHeight: '380px',
		overflowY: 'auto',
		paddingRight: '6px',
	},
	inputArea: {
		width: '100%',
	},
};
