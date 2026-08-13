import React from 'react';
import { motion } from 'motion/react';

export default function ThinkingAnimation() {
	return (
		<div style={styles.container}>
			<motion.div
				animate={{ scale: [0.8, 1.2, 0.8], opacity: [0.4, 1, 0.4] }}
				transition={{ duration: 1, repeat: Infinity, ease: 'easeInOut' }}
				style={{ ...styles.dot, backgroundColor: '#38bdf8' }}
			/>
			<motion.div
				animate={{ scale: [0.8, 1.2, 0.8], opacity: [0.4, 1, 0.4] }}
				transition={{ duration: 1, repeat: Infinity, delay: 0.2, ease: 'easeInOut' }}
				style={{ ...styles.dot, backgroundColor: '#a855f7' }}
			/>
			<motion.div
				animate={{ scale: [0.8, 1.2, 0.8], opacity: [0.4, 1, 0.4] }}
				transition={{ duration: 1, repeat: Infinity, delay: 0.4, ease: 'easeInOut' }}
				style={{ ...styles.dot, backgroundColor: '#34d399' }}
			/>
			<span style={styles.label}>SYRA is thinking...</span>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '10px 16px',
		borderRadius: '16px',
		background: 'rgba(15, 23, 42, 0.7)',
		border: '1px solid rgba(56, 189, 248, 0.15)',
		width: 'fit-content',
	},
	dot: {
		width: '8px',
		height: '8px',
		borderRadius: '50%',
	},
	label: {
		fontSize: '12px',
		color: '#94a3b8',
		fontWeight: 500,
		marginLeft: '4px',
	},
};
