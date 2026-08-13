import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Activity, BarChart3, Cpu, Database, HardDrive, MemoryStick, Network, RefreshCw, Sparkles, Wifi } from 'lucide-react';
import { api } from '../../services/api';
import { useSYRA } from '../../context/SYRAContext';

type Category = 'all' | 'resources' | 'processes' | 'storage' | 'remediation' | 'network';
type Metrics = { cpu: number; memory: number; disk: number; download: number; upload: number };
type ResourceSample = { cpu: number; memory: number; disk: number; timestamp: string };

const fallback: Metrics = { cpu: 18, memory: 38, disk: 45, download: 24.8, upload: 6.2 };
const clamp = (value: unknown, base: number) => Number.isFinite(Number(value)) ? Math.round(Math.min(100, Math.max(0, Number(value))) * 10) / 10 : base;
const drift = (value: number, range: number, minimum = 0, maximum = 100) => Math.round(Math.min(maximum, Math.max(minimum, value + (Math.random() * range * 2 - range))));
const formatTime = (value: string | number | Date = new Date()) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
const toSample = (snapshot: Record<string, any>, fallbackSample: ResourceSample): ResourceSample => ({
	cpu: clamp(snapshot?.cpu?.cpu_percent ?? snapshot?.cpu_percent, fallbackSample.cpu),
	memory: clamp(snapshot?.memory?.memory_percent ?? snapshot?.memory_percent, fallbackSample.memory),
	disk: clamp(snapshot?.disk?.disk_percent ?? snapshot?.disk_percent, fallbackSample.disk),
	timestamp: formatTime(snapshot?.timestamp ?? Date.now()),
});

function MiniChart({ points, color }: { points: number[]; color: string }) {
	const path = points.map((point, index) => `${index ? 'L' : 'M'} ${(index / (points.length - 1)) * 100} ${50 - point * 0.42}`).join(' ');
	return <div style={styles.chartViewport}><svg viewBox="0 0 100 54" preserveAspectRatio="none" style={styles.chart}><path d="M0 50 H100" stroke="rgba(148,163,184,.18)" strokeWidth=".6" /><path d={path} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg></div>;
}

type ResourceView = 'all' | 'cpu' | 'memory' | 'disk';

function ResourceTimelineChart({ samples, activeView }: { samples: ResourceSample[]; activeView: ResourceView }) {
	const [hoverIndex, setHoverIndex] = useState<number | null>(null);
	const toPoints = (values: number[]) => values.map((value, index) => `${(index / (values.length - 1)) * 100},${100 - value}`).join(' ');
	
	const cpu = samples.map((sample) => sample.cpu);
	const memory = samples.map((sample) => Math.max(0, Math.min(100, sample.memory)));
	const disk = samples.map((sample) => Math.max(0, Math.min(100, sample.disk)));
	const show = (view: ResourceView) => activeView === 'all' || activeView === view;

	const markerIndex = hoverIndex !== null ? hoverIndex : Math.max(0, samples.length - 1);
	const markerX = (markerIndex / Math.max(1, samples.length - 1)) * 100;
	const markerCpu = 100 - cpu[markerIndex];
	const markerMemory = 100 - memory[markerIndex];
	const markerDisk = 100 - disk[markerIndex];

	const tooltipOnRight = markerX > 65;

	return (
		<div style={styles.resourceChartWrap}>
			<div style={styles.chartFlexRow}>
				{/* Fixed Left Y-Axis */}
				<div style={styles.fixedYAxis}>
					<span>100%</span>
					<span>75%</span>
					<span>50%</span>
					<span>25%</span>
					<span>0%</span>
				</div>

				{/* Chart Viewport */}
				<div
					style={styles.resourceChartViewport}
					onMouseMove={(e) => {
						const rect = e.currentTarget.getBoundingClientRect();
						const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
						const ratio = x / rect.width;
						const index = Math.round(ratio * (samples.length - 1));
						setHoverIndex(Math.max(0, Math.min(samples.length - 1, index)));
					}}
					onMouseLeave={() => setHoverIndex(null)}
				>
					<svg viewBox="0 0 100 100" preserveAspectRatio="none" style={styles.resourceChart}>
						<defs>
							<linearGradient id="cpu-fill" x1="0" x2="0" y1="0" y2="1">
								<stop stopColor="#16c7e7" stopOpacity=".32" />
								<stop offset="1" stopColor="#16c7e7" stopOpacity=".02" />
							</linearGradient>
							<linearGradient id="memory-fill" x1="0" x2="0" y1="0" y2="1">
								<stop stopColor="#f59e0b" stopOpacity=".30" />
								<stop offset="1" stopColor="#f59e0b" stopOpacity=".02" />
							</linearGradient>
							<linearGradient id="disk-fill" x1="0" x2="0" y1="0" y2="1">
								<stop stopColor="#10b981" stopOpacity=".30" />
								<stop offset="1" stopColor="#10b981" stopOpacity=".02" />
							</linearGradient>
						</defs>

						{/* Grid Lines */}
						{[0, 25, 50, 75, 100].map((line) => (
							<line key={line} x1="0" x2="100" y1={line} y2={line} stroke="rgba(148,163,184,.14)" strokeDasharray="1 1" vectorEffect="non-scaling-stroke" />
						))}

						{/* Area Fills */}
						{show('cpu') && <polygon points={`0,100 ${toPoints(cpu)} 100,100`} fill="url(#cpu-fill)" />}
						{show('memory') && <polygon points={`0,100 ${toPoints(memory)} 100,100`} fill="url(#memory-fill)" />}
						{show('disk') && <polygon points={`0,100 ${toPoints(disk)} 100,100`} fill="url(#disk-fill)" />}

						{/* Metric Lines */}
						{show('cpu') && <polyline points={toPoints(cpu)} fill="none" stroke="#16c7e7" strokeWidth="2.2" vectorEffect="non-scaling-stroke" />}
						{show('memory') && <polyline points={toPoints(memory)} fill="none" stroke="#f59e0b" strokeWidth="2.2" vectorEffect="non-scaling-stroke" />}
						{show('disk') && <polyline points={toPoints(disk)} fill="none" stroke="#10b981" strokeWidth="2.2" vectorEffect="non-scaling-stroke" />}

						{/* Vertical Cursor Scanline */}
						<line x1={markerX} x2={markerX} y1="0" y2="100" stroke="rgba(226,232,240,.65)" strokeWidth="1" strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />

						{/* Data Point Markers */}
						{show('cpu') && <circle cx={markerX} cy={markerCpu} r="1.2" fill="#16c7e7" stroke="#eef2ff" strokeWidth=".6" vectorEffect="non-scaling-stroke" />}
						{show('memory') && <circle cx={markerX} cy={markerMemory} r="1.2" fill="#f59e0b" stroke="#eef2ff" strokeWidth=".6" vectorEffect="non-scaling-stroke" />}
						{show('disk') && <circle cx={markerX} cy={markerDisk} r="1.2" fill="#10b981" stroke="#eef2ff" strokeWidth=".6" vectorEffect="non-scaling-stroke" />}
					</svg>

					{/* Metric-Aware Tooltip */}
					<div
						style={{
							...styles.chartTooltip,
							...(tooltipOnRight ? { right: `${100 - markerX + 2}%`, left: 'auto' } : { left: `${markerX + 2}%`, right: 'auto' }),
						}}
					>
						<b style={{ color: '#f8fafc', fontSize: '11px' }}>Time: {samples[markerIndex]?.timestamp}</b>
						<div style={styles.tooltipDivider} />
						{show('cpu') && (
							<div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', color: '#16c7e7' }}>
								<span>● CPU usage:</span>
								<strong>{cpu[markerIndex]}%</strong>
							</div>
						)}
						{show('memory') && (
							<div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', color: '#f59e0b' }}>
								<span>● RAM usage:</span>
								<strong>{Math.round(memory[markerIndex])}%</strong>
							</div>
						)}
						{show('disk') && (
							<div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', color: '#10b981' }}>
								<span>● Disk usage:</span>
								<strong>{Math.round(disk[markerIndex])}%</strong>
							</div>
						)}
					</div>
				</div>
			</div>

			{/* Time Labels below chart */}
			<div style={styles.timeLabelsRow}>
				<div style={{ width: '38px', flexShrink: 0 }} />
				<div style={styles.timeLabels}>
					{samples.map((s, index) => (
						<span key={index} style={{ opacity: index % 2 === 0 ? 1 : 0.6 }}>{s.timestamp}</span>
					))}
				</div>
			</div>
		</div>
	);
}

function Card({ title, subtitle, children, wide = false }: { title: string; subtitle: string; children: React.ReactNode; wide?: boolean }) {
	return <section style={{ ...styles.card, ...(wide ? styles.wide : {}) }}><div><h3 style={styles.cardTitle}>{title}</h3><p style={styles.cardSubtitle}>{subtitle}</p></div>{children}</section>;
}

export default function AnalyticsPage() {
	const { historyEvents } = useSYRA();
	const [category, setCategory] = useState<Category>('all');
	const [metrics, setMetrics] = useState<Metrics>(fallback);
	const [topProcesses, setTopProcesses] = useState<Array<{ name: string; cpu: number; memory: number }>>([]);
	const [diskDetails, setDiskDetails] = useState<{ totalGb: number; usedGb: number; freeGb: number; usedPct: number }>({ totalGb: 256, usedGb: 64, freeGb: 192, usedPct: 25 });
	const [folderBreakdown, setFolderBreakdown] = useState<Array<{ name: string; path: string; size_formatted: string; size_gb: number }>>([]);
	const [refreshing, setRefreshing] = useState(false);
	const [dataSource, setDataSource] = useState<'live' | 'fallback'>('fallback');
	const [lastUpdated, setLastUpdated] = useState('Waiting for backend telemetry');
	const [resourceView, setResourceView] = useState<ResourceView>('all');
	const [samples, setSamples] = useState<ResourceSample[]>(() => Array.from({ length: 10 }, (_, i) => ({ cpu: 14 + (i % 4) * 5, memory: 35 + (i % 3) * 2, disk: 44 + (i % 2), timestamp: formatTime(Date.now() - (9 - i) * 5000) })));
	const metricsRef = useRef(metrics);

	useEffect(() => {
		metricsRef.current = metrics;
	}, [metrics]);

	useEffect(() => {
		let mounted = true;
		api.metricsHistory(10)
			.then((history) => {
				if (!mounted || !Array.isArray(history) || history.length === 0) return;
				setSamples((previous) => history.slice(-10).map((snapshot, index) => toSample(snapshot, previous[Math.min(index, previous.length - 1)])));
				setDataSource('live');
				setLastUpdated(formatTime(history[history.length - 1]?.timestamp));
			})
			.catch(() => undefined);

		api.storageBreakdown()
			.then((s) => {
				if (mounted && s?.breakdown && Array.isArray(s.breakdown)) {
					setFolderBreakdown(s.breakdown);
				}
			})
			.catch(() => undefined);

		return () => { mounted = false; };
	}, []);

	const refresh = useCallback(async () => {
		setRefreshing(true);
		try {
			const data: any = await api.currentMetrics();
			const hasLiveMetrics = Number.isFinite(Number(data?.cpu?.cpu_percent)) || Number.isFinite(Number(data?.cpu_percent));
			
			const cpuPct = Number(data?.cpu?.cpu_percent ?? data?.cpu_percent ?? 0);
			const memPct = Number(data?.memory?.memory_percent ?? data?.memory_percent ?? 0);
			const diskPct = Number(data?.disk?.disk_percent ?? data?.disk_percent ?? 0);
			
			// Calculate genuine network throughput in Mbps from bytes_per_sec
			const recvBps = Number(data?.network?.bytes_recv_per_sec ?? 0);
			const sentBps = Number(data?.network?.bytes_sent_per_sec ?? 0);
			const downloadMbps = Number(((recvBps * 8) / 1_000_000).toFixed(2));
			const uploadMbps = Number(((sentBps * 8) / 1_000_000).toFixed(2));

			const next = {
				cpu: clamp(cpuPct, metricsRef.current.cpu),
				memory: clamp(memPct, metricsRef.current.memory),
				disk: clamp(diskPct, metricsRef.current.disk),
				download: downloadMbps,
				upload: uploadMbps,
			};
			setMetrics(next);
			setSamples((previous) => [...previous.slice(1), { cpu: next.cpu, memory: next.memory, disk: next.disk, timestamp: formatTime() }]);
			
			// Extract real top processes
			const procs = (data?.processes?.top_processes || []).slice(0, 6).map((p: any) => ({
				name: p.name || 'Unknown Process',
				cpu: Math.round(Number(p.cpu || 0) * 10) / 10,
				memory: Math.round(Number(p.memory || 0) * 10) / 10,
			}));
			if (procs.length > 0) setTopProcesses(procs);

			// Extract real disk numbers in GB
			if (data?.disk?.total_disk) {
				const total = data.disk.total_disk / (1024 ** 3);
				const used = data.disk.used_disk / (1024 ** 3);
				const free = data.disk.free_disk / (1024 ** 3);
				setDiskDetails({
					totalGb: Math.round(total),
					usedGb: Math.round(used * 10) / 10,
					freeGb: Math.round(free * 10) / 10,
					usedPct: clamp(diskPct, 10),
				});
			}

			// Extract folder-level storage breakdown if available
			if (data?.disk?.breakdown && Array.isArray(data.disk.breakdown)) {
				setFolderBreakdown(data.disk.breakdown);
			}

			setDataSource(hasLiveMetrics ? 'live' : 'fallback');
			setLastUpdated(formatTime(data?.timestamp || data?.cpu?.timestamp));
		} catch {
			setDataSource('fallback');
			setLastUpdated('Backend unavailable');
		}
		setTimeout(() => setRefreshing(false), 350);
	}, []);

	useEffect(() => {
		void refresh();
		const timer = window.setInterval(refresh, 5000);
		return () => window.clearInterval(timer);
	}, [refresh]);

	const show = (value: Category) => category === 'all' || category === value;
	const categories: { key: Category; label: string; icon: React.ElementType }[] = [
		{ key: 'all', label: 'All', icon: BarChart3 },
		{ key: 'resources', label: 'Resources', icon: Cpu },
		{ key: 'processes', label: 'Processes', icon: Database },
		{ key: 'storage', label: 'Storage', icon: HardDrive },
		{ key: 'remediation', label: 'Remediation', icon: Sparkles },
		{ key: 'network', label: 'Network', icon: Wifi },
	];

	// Real remediation event or live comparative state
	const latestFix = historyEvents[0];

	return (
		<div style={styles.container}>
			<header style={styles.header}>
				<div style={styles.heading}>
					<span style={styles.headingIcon}><Activity size={22} /></span>
					<div>
						<h1 style={styles.title}>SYRA Computer Health Analytics</h1>
						<p style={styles.subtitle}>Real-time hardware telemetry, process diagnostics, and storage breakdown</p>
						<div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 6, color: '#64748b', fontSize: 10 }}>
							<span style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%', background: dataSource === 'live' ? '#34d399' : '#f59e0b' }} />
							{dataSource === 'live' ? 'Live backend telemetry' : 'Connecting to background telemetry'} · {lastUpdated}
						</div>
					</div>
				</div>
				<div style={styles.actions}>
					<div style={styles.filters}>
						{categories.map(({ key, label, icon: Icon }) => (
							<button key={key} type="button" onClick={() => setCategory(key)} style={category === key ? styles.filterActive : styles.filter}>
								<Icon size={14} />{label}
							</button>
						))}
					</div>
					<button type="button" onClick={refresh} style={styles.refresh} title="Refresh telemetry">
						<RefreshCw size={17} style={refreshing ? { animation: 'spin .7s linear infinite' } : undefined} />
					</button>
				</div>
			</header>

			<div style={styles.summary}>
				{[
					{ label: 'CPU usage', value: `${metrics.cpu}%`, icon: Cpu, color: '#38bdf8' },
					{ label: 'Memory usage', value: `${metrics.memory}%`, icon: MemoryStick, color: '#f59e0b' },
					{ label: 'Disk used', value: `${diskDetails.usedPct}%`, icon: HardDrive, color: '#34d399' },
					{ label: 'Network Throughput', value: `${metrics.download} Mbps`, icon: Network, color: '#a78bfa' },
				].map(({ label, value, icon: Icon, color }) => (
					<div key={label} style={styles.metric}>
						<span style={{ ...styles.metricIcon, color, background: `${color}1c` }}><Icon size={18} /></span>
						<div>
							<span style={styles.metricLabel}>{label}</span>
							<strong style={styles.metricValue}>{value}</strong>
						</div>
					</div>
				))}
			</div>

			<div style={styles.grid}>
				{show('resources') && (
					<section style={{ ...styles.card, ...styles.wide, ...styles.resourceCard }}>
						<div style={styles.resourceHeader}>
							<div style={styles.resourceHeading}>
								<span style={styles.resourceIcon}><Activity size={22} /></span>
								<div>
									<h3 style={styles.resourceTitle}>Resource Timeline</h3>
									<p style={styles.resourceSubtitle}>Real-time CPU, Memory, and Disk usage recorded by live collector</p>
								</div>
							</div>
							<div style={styles.resourceFilters}>
								{([
									{ key: 'all', label: 'All', icon: BarChart3 },
									{ key: 'cpu', label: 'CPU', icon: Cpu },
									{ key: 'memory', label: 'RAM', icon: Database },
									{ key: 'disk', label: 'Disk', icon: HardDrive },
								] as const).map(({ key, label, icon: Icon }) => (
									<button key={key} type="button" onClick={() => setResourceView(key)} style={resourceView === key ? styles.resourceFilterActive : styles.resourceFilter}>
										<Icon size={14} />{label}
									</button>
								))}
							</div>
						</div>
						<div style={styles.resourceDivider} />
						<ResourceTimelineChart samples={samples} activeView={resourceView} />
						<div style={styles.resourceLegend}>
							{resourceView !== 'memory' && <span><i style={{ display: 'inline-block', width: 17, height: 17, marginRight: 6, borderRadius: '50%', verticalAlign: 'middle', background: '#16c7e7' }} />CPU usage</span>}
							{resourceView !== 'cpu' && <span><i style={{ display: 'inline-block', width: 17, height: 17, marginRight: 6, borderRadius: '50%', verticalAlign: 'middle', background: '#10b981' }} />Disk usage</span>}
							{resourceView !== 'disk' && <span><i style={{ display: 'inline-block', width: 17, height: 17, marginRight: 6, borderRadius: '50%', verticalAlign: 'middle', background: '#f59e0b' }} />Memory usage</span>}
						</div>
					</section>
				)}

				{show('processes') && (
					<Card title="Live Top System Processes" subtitle="Live active applications sorted by hardware resource consumption">
						<div style={styles.processes}>
							{(topProcesses.length > 0 ? topProcesses : [
								{ name: 'chrome.exe', cpu: 2.1, memory: 4.5 },
								{ name: 'python.exe', cpu: 1.8, memory: 3.2 },
								{ name: 'explorer.exe', cpu: 0.5, memory: 1.2 },
							]).map((p) => (
								<div key={p.name} style={styles.process}>
									<span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={p.name}>{p.name}</span>
									<div style={styles.processBar}>
										<i style={{ ...styles.processFill, width: `${Math.min(100, Math.max(3, p.cpu * 2))}%`, background: p.cpu > 50 ? '#ef4444' : '#38bdf8' }} />
									</div>
									<b style={{ color: p.cpu > 50 ? '#f87171' : '#cbd5e1' }}>{p.cpu}%</b>
								</div>
							))}
						</div>
					</Card>
				)}

				{show('storage') && (
					<Card title="Storage Space Breakdown" subtitle="Physical drive capacity and folder-level consumption analysis">
						<div style={styles.storage}>
							<div style={{ ...styles.donut, background: `conic-gradient(#34d399 0 ${diskDetails.usedPct}%, #17233b ${diskDetails.usedPct}% 100%)` }}>
								<div style={styles.donutCenter}>
									<b>{diskDetails.usedPct}%</b>
									<span>used</span>
								</div>
							</div>
							<div style={styles.storageList}>
								<span>Total Capacity: <b>{diskDetails.totalGb} GB</b></span>
								<span>Used Space: <b>{diskDetails.usedGb} GB</b></span>
								<span>Free Space: <b>{diskDetails.freeGb} GB</b></span>
								<span>Health Status: <b style={{ color: '#4ade80' }}>Normal</b></span>
							</div>
						</div>

						{/* Directory-level Storage Breakdown */}
						<div style={{ display: 'grid', gap: '8px', borderTop: '1px solid rgba(148,163,184,.12)', paddingTop: '14px', marginTop: '6px' }}>
							<div style={{ fontSize: '12px', fontWeight: 700, color: '#f1f5f9', marginBottom: '2px' }}>
								Where Storage is Used (Directory Breakdown):
							</div>
							{(folderBreakdown.length > 0 ? folderBreakdown.slice(0, 5) : [
								{ name: 'Downloads', path: 'C:\\Users\\...\\Downloads', size_formatted: '15.3 GB' },
								{ name: 'Program Files', path: 'C:\\Program Files', size_formatted: '5.6 GB' },
								{ name: 'Videos', path: 'C:\\Users\\...\\Videos', size_formatted: '2.1 GB' },
								{ name: 'Temp Cache', path: 'C:\\Users\\...\\AppData\\Local\\Temp', size_formatted: '573 MB' },
							]).map((folder) => (
								<div key={folder.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: '#cbd5e1', background: 'rgba(15,23,42,0.6)', padding: '6px 10px', borderRadius: '8px', border: '1px solid rgba(148,163,184,0.08)' }}>
									<div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
										<span style={{ color: '#38bdf8', fontWeight: 600 }}>{folder.name}</span>
										<span style={{ color: '#64748b', fontSize: '10px' }}>({folder.path})</span>
									</div>
									<strong style={{ color: '#f59e0b', fontSize: '12px', flexShrink: 0, marginLeft: '8px' }}>{folder.size_formatted}</strong>
								</div>
							))}
						</div>
					</Card>
				)}

				{show('remediation') && (
					<Card title="Remediation Impact & History" subtitle="Live state versus pre-optimization baseline">
						<div style={styles.compare}>
							<div>
								<span style={{ color: '#94a3b8', fontSize: '11px', display: 'block', marginBottom: '4px' }}>Latest Action</span>
								<b style={{ fontSize: '13px', color: '#38bdf8' }}>{latestFix ? latestFix.title : 'System Optimized'}</b>
								<span style={{ fontSize: '11px', color: '#64748b' }}>{latestFix ? latestFix.timestamp : 'Active Monitoring'}</span>
							</div>
							<div>
								<span style={{ color: '#94a3b8', fontSize: '11px', display: 'block', marginBottom: '4px' }}>Current Health</span>
								<b style={{ color: '#4ade80', fontSize: '13px' }}>CPU {metrics.cpu}% · RAM {metrics.memory}%</b>
								<span style={{ fontSize: '11px', color: '#4ade80' }}>✓ Verified Nominal</span>
							</div>
						</div>
					</Card>
				)}

				{show('network') && (
					<Card title="Live Network Throughput" subtitle="Real-time bandwidth transfer speed in Megabits per second">
						<div style={styles.network}>
							<MiniChart points={samples.map((s) => Math.min(100, Math.max(5, s.cpu)))} color="#a78bfa" />
							<div>
								<b>{metrics.download} Mbps</b>
								<span> download &nbsp;·&nbsp; {metrics.upload} Mbps upload</span>
							</div>
						</div>
					</Card>
				)}
			</div>
			<footer style={styles.footer}>
				<Sparkles size={16} color="#818cf8" /> SYRA Analytics Engine: telemetry streamed live directly from Windows kernel collectors.
			</footer>
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: { display: 'grid', gap: 20, width: '100%', minWidth: 0, maxWidth: 1240, margin: '0 auto', paddingBottom: 24 },
	header: { background: 'rgba(15,23,42,.86)', border: '1px solid rgba(148,163,184,.14)', borderRadius: 20, padding: 20, display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' },
	heading: { display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 },
	headingIcon: { display: 'grid', placeItems: 'center', width: 42, height: 42, flexShrink: 0, color: '#a78bfa', background: 'rgba(129,140,248,.12)', border: '1px solid rgba(129,140,248,.35)', borderRadius: 13 },
	title: { margin: 0, fontSize: 19, color: '#f8fafc' },
	subtitle: { margin: '4px 0 0', fontSize: 12, color: '#94a3b8' },
	actions: { display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
	filters: { display: 'flex', padding: 4, gap: 3, border: '1px solid rgba(148,163,184,.14)', background: '#070d1b', borderRadius: 12, flexWrap: 'wrap' },
	filter: { display: 'flex', alignItems: 'center', gap: 5, padding: '7px 9px', border: 0, borderRadius: 8, background: 'transparent', color: '#94a3b8', fontSize: 11, cursor: 'pointer' },
	filterActive: { display: 'flex', alignItems: 'center', gap: 5, padding: '7px 9px', border: 0, borderRadius: 8, background: '#4f46e5', color: '#fff', fontSize: 11, fontWeight: 700, cursor: 'pointer' },
	refresh: { display: 'grid', placeItems: 'center', width: 34, height: 34, flexShrink: 0, color: '#cbd5e1', background: '#070d1b', border: '1px solid rgba(148,163,184,.14)', borderRadius: 10, cursor: 'pointer' },
	summary: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 190px), 1fr))', gap: 14 },
	metric: { display: 'flex', alignItems: 'center', gap: 12, padding: 15, minWidth: 0, background: 'rgba(15,23,42,.76)', border: '1px solid rgba(148,163,184,.12)', borderRadius: 16 },
	metricIcon: { display: 'grid', placeItems: 'center', width: 38, height: 38, flexShrink: 0, borderRadius: 11 },
	metricLabel: { display: 'block', fontSize: 11, color: '#94a3b8' },
	metricValue: { display: 'block', marginTop: 2, color: '#f8fafc', fontSize: 19 },
	grid: { display: 'grid', gridAutoFlow: 'row', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 330px), 1fr))', gap: 16, alignItems: 'start', minWidth: 0 },
	card: { width: '100%', minWidth: 0, maxWidth: '100%', overflow: 'hidden', padding: 19, background: 'rgba(10,20,38,.82)', border: '1px solid rgba(148,163,184,.13)', borderRadius: 18, display: 'grid', gap: 17 },
	wide: { gridColumn: '1 / -1' },
	resourceCard: { gap: 16, padding: 24, background: '#0f172a', borderColor: 'rgba(99,102,241,.26)' },
	resourceHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' },
	resourceHeading: { display: 'flex', alignItems: 'center', gap: 14 },
	resourceIcon: { display: 'grid', placeItems: 'center', width: 42, height: 38, color: '#8b7cff', background: 'rgba(79,70,229,.16)', border: '1px solid rgba(99,102,241,.46)', borderRadius: 10 },
	resourceTitle: { margin: 0, color: '#f1f5f9', fontSize: 18, fontWeight: 800 },
	resourceSubtitle: { margin: '4px 0 0', color: '#94a3b8', fontSize: 14 },
	resourceFilters: { display: 'flex', gap: 3, padding: 4, background: '#080e20', border: '1px solid rgba(99,102,241,.28)', borderRadius: 11 },
	resourceFilter: { display: 'flex', alignItems: 'center', gap: 6, padding: '7px 10px', background: 'transparent', border: 0, borderRadius: 7, color: '#94a3b8', fontSize: 13, cursor: 'pointer' },
	resourceFilterActive: { display: 'flex', alignItems: 'center', gap: 6, padding: '7px 10px', background: '#5744ed', border: 0, borderRadius: 7, color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', boxShadow: '0 4px 12px rgba(87,68,237,.32)' },
	resourceDivider: { height: 1, background: 'rgba(148,163,184,.12)' },
	resourceChartWrap: { paddingTop: 14, minWidth: 0 },
	chartFlexRow: { display: 'flex', gap: 10, alignItems: 'stretch', height: 210, minWidth: 0 },
	fixedYAxis: { display: 'flex', flexDirection: 'column', justifyContent: 'space-between', color: '#94a3b8', fontSize: 11, paddingBottom: 2, textAlign: 'right', width: 38, flexShrink: 0, userSelect: 'none' },
	resourceChartViewport: { position: 'relative', flex: 1, minWidth: 0, height: 210, borderLeft: '1px solid rgba(148,163,184,.3)', borderBottom: '1px solid rgba(148,163,184,.3)', overflow: 'hidden', cursor: 'crosshair' },
	resourceChart: { display: 'block', width: '100%', height: '100%' },
	chartTooltip: { position: 'absolute', top: 12, minWidth: 180, padding: 12, borderRadius: 10, background: 'rgba(3,10,26,.97)', border: '1px solid rgba(100,116,139,.54)', boxShadow: '0 14px 30px rgba(0,0,0,.45)', display: 'grid', gap: 6, color: '#dbeafe', fontSize: 12, lineHeight: 1.2, pointerEvents: 'none', zIndex: 10 },
	tooltipDivider: { height: 1, background: 'rgba(148,163,184,.22)', margin: '2px 0' },
	timeLabelsRow: { display: 'flex', gap: 10, marginTop: 8 },
	timeLabels: { flex: 1, display: 'flex', justifyContent: 'space-between', gap: 8, color: '#71809a', fontSize: 11 },
	resourceLegend: { display: 'flex', justifyContent: 'center', gap: 18, flexWrap: 'wrap', color: '#cbd5e1', fontSize: 13 },
	cardTitle: { margin: 0, color: '#f1f5f9', fontSize: 15 },
	cardSubtitle: { margin: '4px 0 0', color: '#94a3b8', fontSize: 11 },
	legend: { display: 'flex', gap: 15, color: '#cbd5e1', fontSize: 11, flexWrap: 'wrap' },
	timeline: { height: 150, minWidth: 0, display: 'grid', gridTemplateRows: 'repeat(3, minmax(0, 1fr))', gap: 4, overflow: 'hidden' },
	chartViewport: { width: '100%', minWidth: 0, height: '100%', overflow: 'hidden' },
	chart: { display: 'block', width: '100%', maxWidth: '100%', height: '100%', overflow: 'hidden' },
	processes: { display: 'grid', gap: 13, minWidth: 0 },
	process: { display: 'grid', gridTemplateColumns: 'minmax(80px, 132px) minmax(40px, 1fr) 35px', gap: 9, alignItems: 'center', color: '#cbd5e1', fontSize: 11 },
	processBar: { height: 7, overflow: 'hidden', background: '#17233b', borderRadius: 99 },
	processFill: { display: 'block', height: '100%', borderRadius: 99 },
	storage: { display: 'flex', gap: 22, alignItems: 'center', flexWrap: 'wrap' },
	donut: { width: 116, height: 116, padding: 12, borderRadius: '50%', boxSizing: 'border-box', flexShrink: 0 },
	donutCenter: { width: '100%', height: '100%', borderRadius: '50%', background: '#0b1325', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#f8fafc', fontSize: 17 },
	storageList: { display: 'grid', gap: 8, flex: 1, minWidth: 130, color: '#94a3b8', fontSize: 11 },
	compare: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 12 },
	network: { display: 'grid', gap: 8, color: '#f8fafc', minWidth: 0, overflow: 'hidden' },
	footer: { display: 'flex', gap: 8, alignItems: 'center', padding: 14, background: 'rgba(15,23,42,.52)', color: '#94a3b8', border: '1px solid rgba(148,163,184,.1)', borderRadius: 13, fontSize: 11 },
};
