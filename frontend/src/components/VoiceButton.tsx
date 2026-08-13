import React from 'react';
import { Mic, MicOff, Volume2 } from 'lucide-react';
import VoiceWave from './VoiceWave';

interface VoiceButtonProps {
	isListening: boolean;
	isSpeaking: boolean;
	onToggleListening: () => void;
	size?: 'normal' | 'large';
}

export default function VoiceButton({
	isListening,
	isSpeaking,
	onToggleListening,
	size = 'large',
}: VoiceButtonProps) {
	return (
		<button
			type="button"
			onClick={onToggleListening}
			style={isListening ? styles.btnListening : styles.btnIdle}
		>
			<div style={styles.iconBox}>
				{isListening ? (
					<Mic size={22} color="#ffffff" />
				) : isSpeaking ? (
					<Volume2 size={22} color="#38bdf8" />
				) : (
					<Mic size={22} color="#38bdf8" />
				)}
			</div>

			<div style={styles.labelBox}>
				<span style={styles.primaryText}>
					{isListening ? 'Listening...' : isSpeaking ? 'SYRA Speaking...' : 'Speak to SYRA'}
				</span>
				<span style={styles.secondaryText}>
					{isListening ? 'Tap to finish' : 'Click microphone or spacebar'}
				</span>
			</div>

			<VoiceWave active={isListening || isSpeaking} />
		</button>
	);
}

const styles: Record<string, React.CSSProperties> = {
	btnIdle: {
		display: 'flex',
		alignItems: 'center',
		gap: '14px',
		padding: '12px 24px',
		borderRadius: '20px',
		background: 'rgba(15, 23, 42, 0.85)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
		color: '#f8fafc',
		cursor: 'pointer',
		transition: 'all 0.25s ease',
		backdropFilter: 'blur(12px)',
	},
	btnListening: {
		display: 'flex',
		alignItems: 'center',
		gap: '14px',
		padding: '12px 24px',
		borderRadius: '20px',
		background: 'linear-gradient(135deg, rgba(225, 29, 72, 0.9) 0%, rgba(190, 18, 60, 0.9) 100%)',
		border: '1px solid rgba(251, 113, 133, 0.4)',
		boxShadow: '0 12px 35px rgba(225, 29, 72, 0.4)',
		color: '#ffffff',
		cursor: 'pointer',
		transition: 'all 0.25s ease',
		backdropFilter: 'blur(12px)',
	},
	iconBox: {
		width: '42px',
		height: '42px',
		borderRadius: '14px',
		background: 'rgba(255, 255, 255, 0.12)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	labelBox: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'flex-start',
		textAlign: 'left',
	},
	primaryText: {
		fontSize: '15px',
		fontWeight: 700,
		letterSpacing: '0.02em',
	},
	secondaryText: {
		fontSize: '11px',
		opacity: 0.75,
		marginTop: '1px',
	},
};
