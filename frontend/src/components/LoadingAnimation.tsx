import React from 'react';
import { motion } from 'motion/react';
import SYRAAvatar from './SYRAAvatar';

interface LoadingAnimationProps {
	message?: string;
}

export default function LoadingAnimation({ message = 'Initializing SYRA Core...' }: LoadingAnimationProps) {
	return (
		<div style={styles.container}>
			<SYRAAvatar state="thinking" size={140} interactive={false} />
			<motion.div
				animate={{ opacity: [0.5, 1, 0.5] }}
				transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
				style={styles.message}
			>
				{message}
			</motion.div>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		justifyContent: 'center',
		gap: '20px',
		padding: '40px',
		minHeight: '260px',
	},
	message: {
		fontSize: '14px',
		fontWeight: 600,
		color: '#38bdf8',
		letterSpacing: '0.05em',
	},
};
