import React, { useState, useEffect } from 'react';
import { Wrench, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, Zap, RefreshCw, BookmarkCheck } from 'lucide-react';
import ConfirmationDialog from '../../components/ConfirmationDialog';
import { api } from '../../services/api';
import { useSYRA } from '../../context/SYRAContext';

interface RemediationPageProps {
	diagnosis?: any;
	onRemediationExecuted?: () => void;
}

export default function RemediationPage({ diagnosis, onRemediationExecuted = () => undefined }: RemediationPageProps) {
	const { recordExecutedRemediation, refreshHistory } = useSYRA();
	const [proposal, setProposal] = useState<any>(null);
	const [isProposing, setIsProposing] = useState(false);
	const [isExecuting, setIsExecuting] = useState(false);
	const [executionResult, setExecutionResult] = useState<any>(null);
	const [verificationResult, setVerificationResult] = useState<any>(null);
	const [isVerifying, setIsVerifying] = useState(false);
	const [showApprovalDialog, setShowApprovalDialog] = useState(false);
	const [approvalState, setApprovalState] = useState<'pending' | 'approved' | 'declined'>('pending');
	const [error, setError] = useState('');

	useEffect(() => {
		void handlePropose();
	}, []);

	async function handlePropose() {
		setIsProposing(true);
		setError('');
		setExecutionResult(null);
		setVerificationResult(null);
		setApprovalState('pending');

		try {
			const latest = diagnosis || await api.latestDiagnosis();
			if (!latest?.root_cause) throw new Error('Run a diagnosis first so SYRA can prepare a safe fix.');
			const data = await api.proposeRemediation(latest.root_cause);
			setProposal(data);
		} catch (err: any) {
			setError(err.message || 'Error creating remediation proposal');
		} finally {
			setIsProposing(false);
		}
	}

	async function handleApproval(approved: boolean) {
		if (!proposal) return;
		setShowApprovalDialog(false);
		if (!approved) {
			try {
				await api.approveRemediation(proposal.action_id, false);
				setApprovalState('declined');
			} catch (err: any) {
				setError(err.message || 'Unable to record your decision');
			}
			return;
		}

		setIsExecuting(true);
		setError('');

		try {
			// Permission must be recorded before the executor will accept the action.
			await api.approveRemediation(proposal.action_id, true);
			setApprovalState('approved');
			const data = await api.executeRemediation(proposal.action_id, proposal.root_cause || '');
			if (!data.success) throw new Error(data.message || 'SYRA could not complete the approved action.');
			setExecutionResult(data);
			
			// Auto trigger verification
			void handleVerify(proposal.action_id);
		} catch (err: any) {
			setError(err.message || 'Error executing remediation');
		} finally {
			setIsExecuting(false);
		}
	}

	async function handleActionChange(action: string) {
		if (!proposal || action === proposal.action) return;
		setIsProposing(true);
		setError('');
		setExecutionResult(null);
		setVerificationResult(null);
		setApprovalState('pending');
		try {
			const data = await api.proposeRemediation(proposal.root_cause, action);
			setProposal(data);
		} catch (err: any) {
			setError(err.message || 'Unable to select that remediation action');
		} finally {
			setIsProposing(false);
		}
	}

	async function handleVerify(actionId: string) {
		setIsVerifying(true);
		try {
			// The collector records a fresh system snapshot every five seconds.
			// Wait for that next sample instead of comparing the action against
			// the snapshot captured immediately before execution.
			await new Promise((resolve) => window.setTimeout(resolve, 6500));
			const data = await api.verifyRemediation(actionId);
			setVerificationResult(data);
			if (proposal) {
				recordExecutedRemediation({
					action: proposal.action,
					rootCause: proposal.root_cause || 'system_slowdown',
					message: data.message,
					resolved: data.resolved,
					before: data.before,
					after: data.after,
				});
				void refreshHistory();
				if (data.resolved) {
					onRemediationExecuted();
				}
			}
		} catch {
			// Ignore verification errors
		} finally {
			setIsVerifying(false);
		}
	}

	return (
		<div style={styles.container}>
			<section style={styles.heroCard}>
				<div style={styles.heroLeft}>
					<div style={styles.iconBox}>
						<Wrench size={24} color="#38bdf8" />
					</div>
					<div>
						<div style={styles.kicker}>AUTOMATED HEALTH REMEDIATION ENGINE</div>
						<h1 style={styles.title}>System Optimization & Issue Mitigation</h1>
						<p style={styles.description}>
							SYRA analyzes detected issues and proposes a safe fix. It never changes your computer until you explicitly approve the action.
						</p>
					</div>
				</div>

				<button
					type="button"
					onClick={handlePropose}
					disabled={isProposing}
					style={styles.btnPrimary}
				>
					<Zap size={16} />
					<span>{isProposing ? 'Analyzing Fixes...' : 'Generate Fix Plan'}</span>
				</button>
			</section>

			{error && <div style={styles.errorBox}>{error}</div>}

			{/* Active Proposal Card */}
			{proposal && (
				<section style={styles.card}>
					<div style={styles.cardHeader}>
						<div style={styles.cardHeaderLeft}>
							<AlertCircle size={20} color="#facc15" />
							<div>
								<h3 style={styles.cardTitle}>Remediation Proposal</h3>
								<div style={styles.cardSubtitle}>Action ID: {proposal.action_id}</div>
							</div>
						</div>
						<span style={styles.tagWarning}>Approval Required</span>
					</div>

					<div style={styles.proposalBody}>
						<div style={styles.fieldBlock}>
							<div style={styles.fieldLabel}>Identified Cause</div>
							<div style={styles.fieldVal}>{proposal.root_cause}</div>
						</div>

						{proposal.alternatives?.length > 1 && (
							<div style={styles.fieldBlock}>
								<div style={styles.fieldLabel}>Choose Action Before Approval</div>
								<select
									value={proposal.action}
									disabled={isProposing || isExecuting}
									onChange={(event) => void handleActionChange(event.target.value)}
									style={styles.actionSelect}
								>
									{proposal.alternatives.map((alternative: any) => <option key={alternative.action} value={alternative.action}>{alternative.action} — {alternative.target?.display_name || 'approved target'}</option>)}
								</select>
							</div>
						)}

						<div style={styles.fieldBlock}>
							<div style={styles.fieldLabel}>Proposed Fix Action</div>
							<div style={{ ...styles.fieldVal, color: '#38bdf8', fontWeight: 600 }}>
								{proposal.action}
							</div>
						</div>

						<div style={styles.fieldBlock}>
							<div style={styles.fieldLabel}>Action Description</div>
							<div style={styles.fieldDesc}>{proposal.description}</div>
						</div>
					</div>

					{!executionResult && approvalState !== 'declined' ? (
						<div style={styles.actionRow}>
							<button
								type="button"
								onClick={() => setShowApprovalDialog(true)}
								disabled={isExecuting}
								style={styles.btnExecute}
							>
								<ShieldCheck size={18} />
								<span>{approvalState === 'approved' ? 'Retry Approved Fix' : 'Review & Approve Fix'}</span>
							</button>
						</div>
					) : approvalState === 'declined' ? (
						<div style={styles.declinedBanner}>You declined this action. SYRA did not change anything on your computer.</div>
					) : (
						<div style={styles.executedBanner}>
							<CheckCircle2 size={20} color="#4ade80" />
							<div style={{ flex: 1 }}>
								<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
									<span style={{ color: '#4ade80', fontWeight: 700 }}>Remediation Action Executed</span>
									<span style={{ fontSize: '11px', color: '#38bdf8', background: 'rgba(56,189,248,0.15)', padding: '2px 8px', borderRadius: '8px', border: '1px solid rgba(56,189,248,0.3)' }}>Verification pending</span>
								</div>
								<div style={{ color: '#cbd5e1', fontSize: '13px', marginTop: '2px' }}>{executionResult.message}</div>
							</div>
						</div>
					)}
				</section>
			)}

			<ConfirmationDialog
				isOpen={showApprovalDialog}
				title="Approve SYRA action?"
				message={proposal ? `${proposal.prompt || proposal.description} This action will only run if you choose Approve. It will not run if you decline.` : ''}
				confirmLabel={isExecuting ? 'Applying Fix...' : 'Approve & Run'}
				cancelLabel="Decline"
				onConfirm={() => void handleApproval(true)}
				onCancel={() => void handleApproval(false)}
			/>

			{/* Verification Metrics Card */}
			{verificationResult && (
				<section style={styles.cardSuccess}>
					<div style={styles.cardHeader}>
						<div style={styles.cardHeaderLeft}>
							<ShieldCheck size={20} color="#4ade80" />
							<div>
								<h3 style={styles.cardTitle}>Post-Fix Health Verification</h3>
								<div style={styles.cardSubtitle}>Telemetry delta verification</div>
							</div>
						</div>
						<span style={verificationResult.resolved ? styles.tagSuccess : styles.tagWarning}>{verificationResult.resolved ? 'Resolved' : 'Needs Monitoring'}</span>
					</div>

					<div style={styles.verifyGrid}>
						<div style={styles.metricComparison}>
							<div style={styles.metricTitle}>CPU Before</div>
							<div style={styles.metricValBefore}>{verificationResult.before?.cpu ?? '—'}%</div>
						</div>
						<div style={styles.arrowBox}>
							<ArrowRight size={24} color="#38bdf8" />
						</div>
						<div style={styles.metricComparison}>
							<div style={styles.metricTitle}>CPU After</div>
							<div style={styles.metricValAfter}>{verificationResult.after?.cpu ?? '—'}%</div>
						</div>
					</div>

					<div style={styles.resourceComparison}>
						<span>Memory: {verificationResult.before?.memory ?? '—'}% → {verificationResult.after?.memory ?? '—'}%</span>
						<span>Disk: {verificationResult.before?.disk ?? '—'}% → {verificationResult.after?.disk ?? '—'}%</span>
					</div>

					<div style={styles.verifyNote}>
						{verificationResult.message}
					</div>
				</section>
			)}
		</div>
	);
}

const styles: Record<string, React.CSSProperties> = {
	container: {
		display: 'grid',
		gap: '20px',
	},
	heroCard: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(10, 20, 38, 0.85)',
		border: '1px solid rgba(56, 189, 248, 0.18)',
		boxShadow: '0 20px 50px rgba(0, 0, 0, 0.35)',
		backdropFilter: 'blur(16px)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		gap: '20px',
		flexWrap: 'wrap',
	},
	heroLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '16px',
		maxWidth: '650px',
	},
	iconBox: {
		width: '50px',
		height: '50px',
		borderRadius: '14px',
		background: 'rgba(56, 189, 248, 0.12)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexShrink: 0,
	},
	kicker: {
		fontSize: '11px',
		letterSpacing: '0.12em',
		color: '#38bdf8',
		fontWeight: 700,
	},
	title: {
		margin: '4px 0',
		fontSize: '22px',
		fontWeight: 800,
		color: '#f8fafc',
	},
	description: {
		margin: 0,
		fontSize: '13px',
		color: '#94a3b8',
		lineHeight: 1.5,
	},
	btnPrimary: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '12px 22px',
		borderRadius: '12px',
		border: 'none',
		background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
		color: '#fff',
		fontWeight: 700,
		fontSize: '13px',
		cursor: 'pointer',
		boxShadow: '0 10px 25px rgba(37, 99, 235, 0.35)',
	},
	errorBox: {
		padding: '14px 18px',
		borderRadius: '14px',
		background: 'rgba(127, 29, 29, 0.42)',
		border: '1px solid rgba(248, 113, 113, 0.3)',
		color: '#fecaca',
		fontSize: '13px',
	},
	card: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(15, 23, 42, 0.8)',
		border: '1px solid rgba(148, 163, 184, 0.15)',
		display: 'grid',
		gap: '18px',
	},
	cardSuccess: {
		padding: '24px',
		borderRadius: '20px',
		background: 'rgba(6, 78, 59, 0.25)',
		border: '1px solid rgba(52, 211, 153, 0.3)',
		display: 'grid',
		gap: '18px',
	},
	cardHeader: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
	},
	cardHeaderLeft: {
		display: 'flex',
		alignItems: 'center',
		gap: '12px',
	},
	cardTitle: {
		margin: 0,
		fontSize: '17px',
		fontWeight: 700,
		color: '#f8fafc',
	},
	cardSubtitle: {
		fontSize: '12px',
		color: '#94a3b8',
	},
	tagWarning: {
		padding: '4px 10px',
		borderRadius: '20px',
		background: 'rgba(234, 179, 8, 0.15)',
		border: '1px solid rgba(234, 179, 8, 0.3)',
		color: '#facc15',
		fontSize: '11px',
		fontWeight: 700,
	},
	tagSuccess: {
		padding: '4px 10px',
		borderRadius: '20px',
		background: 'rgba(34, 197, 94, 0.15)',
		border: '1px solid rgba(34, 197, 94, 0.3)',
		color: '#4ade80',
		fontSize: '11px',
		fontWeight: 700,
	},
	proposalBody: {
		display: 'grid',
		gap: '14px',
		padding: '16px',
		borderRadius: '14px',
		background: 'rgba(10, 20, 38, 0.6)',
		border: '1px solid rgba(148, 163, 184, 0.08)',
	},
	fieldBlock: {
		display: 'grid',
		gap: '4px',
	},
	fieldLabel: {
		fontSize: '11px',
		textTransform: 'uppercase',
		letterSpacing: '0.05em',
		color: '#64748b',
		fontWeight: 700,
	},
	fieldVal: {
		fontSize: '14px',
		color: '#f1f5f9',
	},
	fieldDesc: {
		fontSize: '13px',
		color: '#cbd5e1',
	},
	actionSelect: {
		width: '100%',
		padding: '10px 12px',
		borderRadius: '10px',
		background: 'rgba(10, 15, 28, 0.9)',
		border: '1px solid rgba(56, 189, 248, 0.25)',
		color: '#f8fafc',
		fontSize: '13px',
	},
	actionRow: {
		display: 'flex',
		justifyContent: 'flex-end',
	},
	btnExecute: {
		display: 'flex',
		alignItems: 'center',
		gap: '8px',
		padding: '12px 24px',
		borderRadius: '12px',
		border: 'none',
		background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
		color: '#fff',
		fontWeight: 700,
		fontSize: '13px',
		cursor: 'pointer',
		boxShadow: '0 8px 20px rgba(34, 197, 94, 0.3)',
	},
	executedBanner: {
		display: 'flex',
		alignItems: 'center',
		gap: '12px',
		padding: '14px 18px',
		borderRadius: '12px',
		background: 'rgba(34, 197, 94, 0.12)',
		border: '1px solid rgba(34, 197, 94, 0.25)',
	},
	declinedBanner: {
		padding: '14px 18px',
		borderRadius: '12px',
		background: 'rgba(71, 85, 105, 0.2)',
		border: '1px solid rgba(148, 163, 184, 0.25)',
		color: '#cbd5e1',
		fontSize: '13px',
	},
	verifyGrid: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		gap: '32px',
		padding: '20px',
		borderRadius: '14px',
		background: 'rgba(10, 20, 38, 0.6)',
	},
	metricComparison: {
		textAlign: 'center',
	},
	metricTitle: {
		fontSize: '12px',
		color: '#94a3b8',
		marginBottom: '4px',
	},
	metricValBefore: {
		fontSize: '28px',
		fontWeight: 800,
		color: '#f87171',
	},
	metricValAfter: {
		fontSize: '28px',
		fontWeight: 800,
		color: '#4ade80',
	},
	arrowBox: {
		padding: '10px',
		borderRadius: '50%',
		background: 'rgba(56, 189, 248, 0.1)',
	},
	verifyNote: {
		textAlign: 'center',
		fontSize: '13px',
		color: '#cbd5e1',
	},
	resourceComparison: {
		display: 'flex',
		justifyContent: 'center',
		gap: '24px',
		flexWrap: 'wrap',
		color: '#cbd5e1',
		fontSize: '13px',
	},
};
