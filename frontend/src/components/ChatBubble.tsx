import React from 'react';
import { Bot, User, Sparkles } from 'lucide-react';
import { Message } from '../types/types';

interface ChatBubbleProps {
	message: Message;
	onPromptClick?: (prompt: string) => void;
}

export default function ChatBubble({ message, onPromptClick }: ChatBubbleProps) {
	const isSyra = message.sender === 'syra';

	return (
		<div style={isSyra ? styles.syraWrapper : styles.userWrapper}>
			<div style={styles.headerRow}>
				<div style={isSyra ? styles.syraTag : styles.userTag}>
					{isSyra ? <Bot size={13} color="#38bdf8" /> : <User size={13} color="#93c5fd" />}
					<span>{isSyra ? 'SYRA' : 'You'}</span>
				</div>
				<span style={styles.timestamp}>{message.timestamp}</span>
			</div>

			<div style={isSyra ? styles.syraBubble : styles.userBubble}>
				<div style={styles.messageText}>{message.text}</div>
			</div>

			{isSyra && message.suggestedPrompts && message.suggestedPrompts.length > 0 && (
				<div style={styles.promptsRow}>
					{message.suggestedPrompts.map((prompt, idx) => (
						<button
							key={idx}
							type="button"
							onClick={() => onPromptClick?.(prompt)}
							style={styles.promptBtn}
						>
							<Sparkles size={12} color="#38bdf8" />
							<span>{prompt}</span>
						</button>
					))}
				</div>
			)}
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	syraWrapper: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'flex-start',
		gap: '6px',
		maxWidth: '85%',
		marginRight: 'auto',
	},
	userWrapper: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'flex-end',
		gap: '6px',
		maxWidth: '85%',
		marginLeft: 'auto',
	},
	headerRow: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '0 4px',
	},
	syraTag: {
		display: 'flex',
		alignItems: 'center',
		gap: '5px',
		fontSize: '11px',
		fontWeight: 700,
		color: '#38bdf8',
		letterSpacing: '0.05em',
		textTransform: 'uppercase',
	},
	userTag: {
		display: 'flex',
		alignItems: 'center',
		gap: '5px',
		fontSize: '11px',
		fontWeight: 700,
		color: '#93c5fd',
		letterSpacing: '0.05em',
		textTransform: 'uppercase',
	},
	timestamp: {
		fontSize: '10px',
		color: '#64748b',
	},
	syraBubble: {
		padding: '14px 18px',
		borderRadius: '18px 18px 18px 4px',
		background: 'rgba(15, 23, 42, 0.75)',
		border: '1px solid rgba(56, 189, 248, 0.2)',
		color: '#f8fafc',
		backdropFilter: 'blur(12px)',
		boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
	},
	userBubble: {
		padding: '14px 18px',
		borderRadius: '18px 18px 4px 18px',
		background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.85) 0%, rgba(29, 78, 216, 0.85) 100%)',
		border: '1px solid rgba(147, 197, 253, 0.3)',
		color: '#ffffff',
		boxShadow: '0 8px 24px rgba(37, 99, 235, 0.25)',
	},
	messageText: {
		fontSize: '14px',
		lineHeight: 1.6,
		whiteSpace: 'pre-wrap',
	},
	promptsRow: {
		display: 'flex',
		flexWrap: 'wrap',
		gap: '8px',
		marginTop: '4px',
	},
	promptBtn: {
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		padding: '6px 12px',
		borderRadius: '12px',
		background: 'rgba(30, 41, 59, 0.8)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		color: '#cbd5e1',
		fontSize: '12px',
		fontWeight: 500,
		cursor: 'pointer',
		transition: 'all 0.2s ease',
	},
};
