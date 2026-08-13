import React from 'react';
import { motion } from 'motion/react';

interface VoiceWaveProps {
	active: boolean;
	barCount?: number;
}

export default function VoiceWave({ active, barCount = 7 }: VoiceWaveProps) {
	const bars = Array.from({ length: barCount });

	return (
		<div style={styles.container}>
			{bars.map((_, i) => (
				<motion.div
					key={i}
					animate={{
						height: active ? [6, 24, 12, 30, 8, 20, 6][(i + Math.floor(Math.random() * 3)) % 7] : 4,
						opacity: active ? 1 : 0.4,
					}}
					transition={{
						duration: active ? 0.4 + (i % 3) * 0.15 : 0.2,
						repeat: active ? Infinity : 0,
						repeatType: 'mirror',
						ease: 'easeInOut',
					}}
					style={{
						width: '3.5px',
						borderRadius: '4px',
						background: active ? '#38bdf8' : '#64748b',
					}}
				/>
			))}
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		gap: '3px',
		height: '32px',
		padding: '0 6px',
	},
};
