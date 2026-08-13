import React from 'react';
import { AvatarState } from '../types/types';

interface SYRAAvatarProps {
	state: AvatarState;
	size?: number;
	onClick?: () => void;
	interactive?: boolean;
}

export default function SYRAAvatar({
	state = 'idle',
	size = 180,
	onClick,
	interactive = true,
}: SYRAAvatarProps) {
	const getGlowColors = () => {
		switch (state) {
			case 'listening':
				return {
					bg: 'radial-gradient(circle at 35% 30%, #38bdf8 0%, #0284c7 50%, #0369a1 100%)',
					border: '#38bdf8',
					eye: '#0284c7',
					outer: 'rgba(56, 189, 248, 0.5)',
					ring: '#7dd3fc',
				};
			case 'thinking':
				return {
					bg: 'radial-gradient(circle at 35% 30%, #e879f9 0%, #c084fc 45%, #7e22ce 100%)',
					border: '#f0abfc',
					eye: '#7e22ce',
					outer: 'rgba(232, 121, 249, 0.5)',
					ring: '#f5d0fe',
				};
			case 'speaking':
				return {
					bg: 'radial-gradient(circle at 35% 30%, #22d3ee 0%, #0284c7 45%, #1d4ed8 100%)',
					border: '#67e8f9',
					eye: '#0369a1',
					outer: 'rgba(34, 211, 238, 0.6)',
					ring: '#a5f3fc',
				};
			case 'alert':
				return {
					bg: 'radial-gradient(circle at 35% 30%, #f87171 0%, #dc2626 50%, #991b1b 100%)',
					border: '#fca5a5',
					eye: '#991b1b',
					outer: 'rgba(248, 113, 113, 0.6)',
					ring: '#fecdd3',
				};
			case 'monitoring':
				return {
					bg: 'radial-gradient(circle at 35% 30%, #34d399 0%, #059669 50%, #064e3b 100%)',
					border: '#6ee7b7',
					eye: '#064e3b',
					outer: 'rgba(52, 211, 153, 0.45)',
					ring: '#a7f3d0',
				};
			case 'idle':
			default:
				return {
					bg: 'radial-gradient(circle at 35% 30%, #38bdf8 0%, #2563eb 55%, #4338ca 100%)',
					border: '#38bdf8',
					eye: '#1e40af',
					outer: 'rgba(56, 189, 248, 0.45)',
					ring: '#60a5fa',
				};
		}
	};

	const colors = getGlowColors();

	return (
		<div
			onClick={onClick}
			style={{
				position: 'relative',
				width: `${size}px`,
				height: `${size}px`,
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'center',
				cursor: interactive ? 'pointer' : 'default',
				userSelect: 'none',
			}}
		>
			{/* Static Outer Glow */}
			<div
				style={{
					position: 'absolute',
					inset: '-15%',
					borderRadius: '50%',
					background: `radial-gradient(circle, ${colors.outer} 0%, rgba(0,0,0,0) 70%)`,
					pointerEvents: 'none',
					opacity: 0.5,
				}}
			/>

			{/* Static Outer Dotted Ring */}
			<div
				style={{
					position: 'absolute',
					width: '105%',
					height: '105%',
					borderRadius: '50%',
					pointerEvents: 'none',
				}}
			>
				<svg width="100%" height="100%" viewBox="0 0 100 100">
					<circle
						cx="50"
						cy="50"
						r="48"
						fill="none"
						stroke={colors.ring}
						strokeWidth="0.9"
						strokeDasharray="3 8"
						opacity="0.6"
					/>
					<circle cx="50" cy="2" r="2.5" fill={colors.border} />
					<circle cx="98" cy="50" r="1.8" fill={colors.ring} />
					<circle cx="2" cy="50" r="1.8" fill={colors.ring} />
				</svg>
			</div>

			{/* Static Center Orb with Headset Bot Icon */}
			<div
				style={{
					width: `${size * 0.8}px`,
					height: `${size * 0.8}px`,
					borderRadius: '50%',
					background: colors.bg,
					boxShadow: `0 0 35px ${colors.outer}, inset 0 0 15px rgba(255,255,255,0.45)`,
					border: `2.5px solid ${colors.border}`,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
					position: 'relative',
					overflow: 'hidden',
				}}
			>
				{/* Top Inner Glass Reflection */}
				<div
					style={{
						position: 'absolute',
						top: '5%',
						left: '15%',
						width: '70%',
						height: '35%',
						borderRadius: '50%',
						background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0) 100%)',
						pointerEvents: 'none',
					}}
				/>

				{/* The SYRA Headset Bot Icon */}
				<svg
					viewBox="0 0 100 100"
					style={{
						width: '58%',
						height: '58%',
						filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.25))',
						position: 'relative',
						zIndex: 2,
					}}
				>
					{/* Headband over head */}
					<path
						d="M 22 42 C 22 18, 78 18, 78 42"
						fill="none"
						stroke="#ffffff"
						strokeWidth="7"
						strokeLinecap="round"
					/>

					{/* Left Ear Pad */}
					<rect x="9" y="34" width="13" height="28" rx="6.5" fill="#ffffff" />

					{/* Right Ear Pad */}
					<rect x="78" y="34" width="13" height="28" rx="6.5" fill="#ffffff" />

					{/* Head Screen Container */}
					<rect x="21" y="24" width="58" height="52" rx="16" fill="#ffffff" />

					{/* Left Eye Arc */}
					<path
						d="M 31 43 Q 37 34 43 43"
						fill="none"
						stroke={colors.eye}
						strokeWidth="3.8"
						strokeLinecap="round"
					/>

					{/* Right Eye Arc */}
					<path
						d="M 57 43 Q 63 34 69 43"
						fill="none"
						stroke={colors.eye}
						strokeWidth="3.8"
						strokeLinecap="round"
					/>

					{/* Happy Smiling Mouth Arc */}
					<path
						d="M 38 56 Q 50 68 62 56"
						fill="none"
						stroke={colors.eye}
						strokeWidth="3.8"
						strokeLinecap="round"
					/>

					{/* Microphone Stem */}
					<path
						d="M 84 58 L 84 74 C 84 84, 68 85, 52 85"
						fill="none"
						stroke="#ffffff"
						strokeWidth="5"
						strokeLinecap="round"
						strokeLinejoin="round"
					/>

					{/* Microphone Capsule */}
					<rect x="42" y="80" width="15" height="10" rx="4" fill="#ffffff" />
				</svg>
			</div>
		</div>
	);
}

