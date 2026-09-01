const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `HTTP Error ${response.status}: ${response.statusText}`;
      throw new Error(message);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Request failed on ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Demo Seed/Reset
  resetDatabase: () => request('/api/demo/reset', { method: 'POST' }),

  // Recovery Cases
  getCases: () => request('/api/cases'),
  getCase: (caseId) => request(`/api/cases/${caseId}`),
  runCase: (caseId) => request(`/api/cases/${caseId}/run`, { method: 'POST' }),
  triggerScheduled: (caseId) => request(`/api/cases/${caseId}/trigger_scheduled`, { method: 'POST' }),

  // Human Review Queue
  getPendingApprovals: () => request('/api/approvals/pending'),
  getApprovalContext: (caseId) => request(`/api/approvals/${caseId}`),
  approveCase: (caseId, reviewerId, reason) =>
    request(`/api/approvals/${caseId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ reviewer_id: reviewerId, reason }),
    }),
  rejectCase: (caseId, reviewerId, reason) =>
    request(`/api/approvals/${caseId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reviewer_id: reviewerId, reason }),
    }),

  // Recovery Batches
  getBatches: () => request('/api/batches'),
  createBatch: (batchName, caseIds = null) =>
    request('/api/batches', {
      method: 'POST',
      body: JSON.stringify({ batch_name: batchName, case_ids: caseIds }),
    }),
  runBatch: (batchId) => request(`/api/batches/${batchId}/run`, { method: 'POST' }),
  getBatch: (batchId) => request(`/api/batches/${batchId}`),
  getBatchImpact: (batchId) => request(`/api/batches/${batchId}/impact`),

  // Audit Trails
  getCaseAuditTrail: (caseId) => request(`/api/audit/cases/${caseId}`),
  getBatchAuditTrail: (batchId) => request(`/api/audit/batches/${batchId}`),
};
