import React, { useState, FormEvent } from 'react';
import { Send, Mic } from 'lucide-react';
import VoiceButton from './VoiceButton';

interface ChatInputProps {
	onSendMessage: (text: string) => void;
	isListening: boolean;
	isSpeaking: boolean;
	onToggleListening: () => void;
	disabled?: boolean;
}

export default function ChatInput({
	onSendMessage,
	isListening,
	isSpeaking,
	onToggleListening,
	disabled = false,
}: ChatInputProps) {
	const [text, setText] = useState('');

	function handleSubmit(e: FormEvent) {
		e.preventDefault();
		if (text.trim() && !disabled) {
			onSendMessage(text.trim());
			setText('');
		}
	}

	return (
		<div style={styles.container}>
			<VoiceButton
				isListening={isListening}
				isSpeaking={isSpeaking}
				onToggleListening={onToggleListening}
			/>

			<form onSubmit={handleSubmit} style={styles.form}>
				<input
					type="text"
					value={text}
					onChange={(e) => setText(e.target.value)}
					placeholder="Type a message to SYRA..."
					disabled={disabled}
					style={styles.input}
				/>
				<button
					type="submit"
					disabled={!text.trim() || disabled}
					style={text.trim() && !disabled ? styles.sendActive : styles.sendDisabled}
				>
					<Send size={16} />
				</button>
			</form>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'flex',
		alignItems: 'center',
		gap: '14px',
		width: '100%',
		flexWrap: 'wrap',
	},
	form: {
		flex: 1,
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		background: 'rgba(15, 23, 42, 0.75)',
		border: '1px solid rgba(148, 163, 184, 0.15)',
		borderRadius: '20px',
		padding: '6px 8px 6px 18px',
		backdropFilter: 'blur(12px)',
		minWidth: '260px',
	},
	input: {
		flex: 1,
		background: 'transparent',
		border: 'none',
		outline: 'none',
		color: '#f8fafc',
		fontSize: '14px',
		fontFamily: 'inherit',
	},
	sendActive: {
		width: '38px',
		height: '38px',
		borderRadius: '14px',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		border: 'none',
		color: '#ffffff',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		cursor: 'pointer',
		boxShadow: '0 4px 14px rgba(56, 189, 248, 0.3)',
	},
	sendDisabled: {
		width: '38px',
		height: '38px',
		borderRadius: '14px',
		background: 'rgba(51, 65, 85, 0.3)',
		border: 'none',
		color: '#64748b',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		cursor: 'not-allowed',
	},
};
