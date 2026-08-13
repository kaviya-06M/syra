const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export type ChatResponse = {
	session_id: string;
	reply: string;
	used_diagnosis: boolean;
	llm_ready?: boolean;
	llm_error?: string | null;
	ml_analysis?: Record<string, unknown>;
};

export type DiagnosisResponse = {
	root_cause: string | null;
	confidence: number;
	evidence: string[];
	path?: string[];
	all_candidates?: Record<string, number>;
	matched_rules?: Array<{ rule_id: string; symptom: string; severity: string }>;
	timestamp?: string;
};

export type RemediationProposal = {
	action_id: string;
	prompt: string;
	action?: string;
	action_name?: string;
	root_cause?: string;
	description?: string;
	alternatives?: Array<{ action: string; description: string; target: Record<string, unknown> }>;
};

export type RemediationResult = {
	success: boolean;
	message?: string;
	action_id?: string;
	root_cause?: string;
	timestamp?: string;
};

export type VerificationResult = {
	resolved: boolean;
	still_critical: boolean;
	checks: Record<string, boolean>;
	root_cause?: string;
	rollback?: Record<string, unknown>;
	before?: { cpu: number; memory: number; disk: number };
	after?: { cpu: number; memory: number; disk: number };
	message?: string;
	before_timestamp?: string;
	after_timestamp?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(`${API_BASE_URL}${path}`, {
		...init,
		headers: {
			'Content-Type': 'application/json',
			...init?.headers,
		},
	});

	if (!response.ok) {
		const detail = await response.text();
		throw new Error(detail || `Backend request failed (${response.status})`);
	}

	return response.json() as Promise<T>;
}

export const api = {
	// ── Health ─────────────────────────────────────────────────────────────
	health: () => request<{ status: string; service: string }>('/api/health'),

	// ── Metrics ────────────────────────────────────────────────────────────
	currentMetrics: () => request<Record<string, unknown>>('/api/metrics/current'),
	metricsHistory: (limit = 50) => request<Array<Record<string, unknown>>>(`/api/metrics/history?limit=${limit}`),
	metricsSummary: () => request<Record<string, unknown>>('/api/metrics/summary'),
	storageBreakdown: (refresh = false) => request<{
		total_disk: number;
		used_disk: number;
		free_disk: number;
		disk_percent: number;
		breakdown: Array<{ name: string; path: string; type: string; size_bytes: number; size_gb: number; size_formatted: string }>;
	}>(`/api/metrics/storage?refresh=${refresh}`),

	// ── Diagnosis ──────────────────────────────────────────────────────────
	latestDiagnosis: () => request<DiagnosisResponse>('/api/diagnosis/latest'),
	runDiagnosis: (eventData?: Record<string, unknown>) =>
		request<DiagnosisResponse>('/api/diagnosis/analyze', {
			method: 'POST',
			body: JSON.stringify({ event_data: eventData }),
		}),

	// ── Remediation ────────────────────────────────────────────────────────
	proposeRemediation: (rootCause?: string, action?: string) =>
		request<RemediationProposal>('/api/remediation/propose', {
			method: 'POST',
			body: JSON.stringify({ root_cause: rootCause, action }),
		}),

	approveRemediation: (actionId: string, approved: boolean) =>
		request<{ success: boolean; status: string }>('/api/remediation/approve', {
			method: 'POST',
			body: JSON.stringify({ action_id: actionId, approved }),
		}),

	executeRemediation: (actionId: string, rootCause: string) =>
		request<RemediationResult>('/api/remediation/execute', {
			method: 'POST',
			body: JSON.stringify({ action_id: actionId, root_cause: rootCause }),
		}),

	verifyRemediation: (actionId: string) =>
		request<VerificationResult>(`/api/remediation/verify/${actionId}`, {
			method: 'POST',
		}),

	// ── Chat (LLM Llama 3.1 70B via NVIDIA NIM) ───────────────────────────
	sendChatMessage: (message: string, sessionId?: string) =>
		request<ChatResponse>('/api/chat/message', {
			method: 'POST',
			body: JSON.stringify({ message, session_id: sessionId }),
		}),

	getChatHistory: (sessionId: string) =>
		request<{ session_id: string; history: Array<{ role: string; content: string }> }>(`/api/chat/history/${sessionId}`),

	// ── History ────────────────────────────────────────────────────────────
	listIncidents: (limit = 20) => request<Array<Record<string, unknown>>>(`/api/history/incidents?limit=${limit}`),
	getHistoryStats: () => request<{ total_incidents: number; resolved: number; unresolved: number }>('/api/history/stats'),
};
