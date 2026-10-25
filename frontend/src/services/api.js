/**
 * frontend/src/services/api.js
 * Production API client connecting the React frontend to the FastAPI backend service.
 * Supports configurable VITE_API_BASE_URL, unified request dispatching, and safe diagnostic error handling.
 */

/**
 * Resolves the active backend API base URL:
 * 1. Explicit VITE_API_BASE_URL environment variable if configured.
 * 2. Defaults to empty string so all requests use relative paths ('/api/...', '/ready', etc.).
 *    In local development, the Vite dev server proxy forwards these to http://127.0.0.1:8000,
 *    guaranteeing that login, session cookies, and analysis submissions share the exact same local origin.
 */
export function getApiBaseUrl() {
  const envUrl = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
  if (envUrl) {
    return envUrl;
  }
  return '';
}

// In-memory session cache for fast tab-switching and ephemeral client retention
const memoryCache = new Map();

/**
 * Unified HTTP request helper with robust error translation and zero secret/path leakage.
 * Relies strictly on HttpOnly cookies for browser authentication session (credentials: 'include').
 */
async function request(endpoint, options = {}) {
  const baseUrl = getApiBaseUrl();
  const url = baseUrl ? `${baseUrl}${endpoint}` : endpoint;
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    'X-Requested-With': 'XMLHttpRequest',
    ...(options.headers || {}),
  };

  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (netErr) {
    const hostLabel = baseUrl || (typeof window !== 'undefined' ? window.location.origin : 'backend');
    throw new Error(
      `Unable to reach the Smart Contract Analyser backend at ${hostLabel}. ` +
      `Please ensure the local FastAPI backend is running on http://127.0.0.1:8000 and that CORS allows requests from this domain.`,
      { cause: netErr }
    );
  }

  const contentType = response.headers.get('content-type') || '';
  const isHtml = contentType.includes('text/html');

  if (response.status === 405) {
    throw new Error(
      `Backend service is not connected (HTTP 405 on ${endpoint}). ` +
      `Please ensure the local FastAPI backend is running on http://127.0.0.1:8000.`
    );
  }

  if (isHtml && !response.ok) {
    throw new Error(
      `Analysis service returned an unexpected response (status ${response.status}). ` +
      `Please verify that the local FastAPI backend service is running on http://127.0.0.1:8000.`
    );
  }

  let data = null;
  if (!isHtml) {
    data = await response.json().catch(() => null);
  }

  if (!response.ok) {
    let errorMessage = `Analysis service error (${response.status})`;

    if (data?.detail) {
      errorMessage = typeof data.detail === 'object'
        ? (data.detail.message || JSON.stringify(data.detail))
        : data.detail;
    } else if (data?.reason) {
      errorMessage = data.reason;
    } else if (response.status === 503) {
      errorMessage = 'Legal-BERT analysis engine is unavailable. Model weights (legal_bert_v3.3.0) are not initialized on the backend.';
    } else if (response.status === 429) {
      errorMessage = 'Rate limit exceeded (maximum 10 submissions per minute). Please wait 60 seconds before submitting again.';
    } else if (response.status === 413) {
      errorMessage = 'Source code exceeds maximum permitted payload size of 1MB.';
    } else if (response.status === 400) {
      errorMessage = 'Invalid or empty Solidity smart contract submitted.';
    } else if (response.status === 422) {
      errorMessage = 'Unsupported or non-Solidity source submitted. Please verify contract syntax.';
    } else if (response.status === 404) {
      errorMessage = `The requested analysis resource was not found (${endpoint}). It may have expired under the 30-minute in-memory retention policy.`;
    } else if (response.status >= 500) {
      errorMessage = 'An internal server error occurred on the backend during analysis processing.';
    }

    const error = new Error(errorMessage);
    error.status = response.status;
    error.detail = data?.detail;
    error.code = data?.detail?.code || (data?.status === 'not_ready' ? 'MODEL_UNAVAILABLE' : undefined);
    throw error;
  }

  return data;
}

export const api = {
  /**
   * Returns current active base URL
   */
  getBaseUrl() {
    return getApiBaseUrl();
  },

  /**
   * Health check endpoint confirming engine readiness and storage policy
   */
  async checkHealth() {
    try {
      const data = await request('/api/v1/health');
      return data || { status: 'offline' };
    } catch (err) {
      return { status: 'offline', error: err.message };
    }
  },

  /**
   * Model readiness probe checking if legal_bert_v3.3.0 checkpoint is initialized
   */
  async checkReadiness() {
    try {
      const data = await request('/ready');
      return data || { status: 'not_ready' };
    } catch (err) {
      return { status: 'not_ready', error: err.message };
    }
  },

  /**
   * Phase 1: Initiate asynchronous Legal-BERT analysis job with real progress tracking
   */
  async startAnalysisJob(sourceCode, contractName = 'Contract.sol', description = '') {
    return await request('/api/v1/analyze/jobs', {
      method: 'POST',
      body: JSON.stringify({
        sourceCode,
        contractName,
        description,
      }),
    });
  },

  /**
   * Phase 1: Upload .sol file directly via multipart form data
   */
  async uploadContractFile(file, contractName = '', description = '') {
    const formData = new FormData();
    formData.append('file', file);
    if (contractName) formData.append('contract_name', contractName);
    if (description) formData.append('description', description);

    const data = await request('/api/v1/analyze/upload', {
      method: 'POST',
      body: formData,
    });

    if (data?.analysisId) {
      memoryCache.set(data.analysisId, data);
      try {
        sessionStorage.setItem(`audit_${data.analysisId}`, JSON.stringify(data));
      } catch (e) {
        console.warn('Session storage write failed:', e);
      }
    }

    return data;
  },

  /**
   * Phase 1: Poll real analysis job status and progress
   */
  async getJobStatus(jobId) {
    const data = await request(`/api/v1/jobs/${jobId}`);
    if (data?.result?.analysisId) {
      memoryCache.set(data.result.analysisId, data.result);
      try {
        sessionStorage.setItem(`audit_${data.result.analysisId}`, JSON.stringify(data.result));
      } catch (e) {
        console.warn('Session storage write failed:', e);
      }
    }
    return data;
  },

  /**
   * Phase 1: Explicitly discard temporary analysis and purge in-memory cache
   */
  async discardAnalysis(analysisId) {
    if (memoryCache.has(analysisId)) {
      memoryCache.delete(analysisId);
    }
    try {
      sessionStorage.removeItem(`audit_${analysisId}`);
    } catch (e) {
      console.warn('Session storage remove failed:', e);
    }

    try {
      await request(`/api/v1/analyze/${analysisId}/discard`, {
        method: 'POST',
      });
    } catch (err) {
      console.warn('Backend discard call failed (may already be purged):', err);
    }
    return { status: 'discarded', analysisId };
  },

  /**
   * Submit Solidity source code for synchronous Legal-BERT analysis
   */
  async analyzeContract(sourceCode, contractName = 'Contract.sol', description = '') {
    const data = await request('/api/v1/analyze', {
      method: 'POST',
      body: JSON.stringify({
        sourceCode,
        contractName,
        description,
      }),
    });

    if (data?.analysisId) {
      memoryCache.set(data.analysisId, data);
      try {
        sessionStorage.setItem(`audit_${data.analysisId}`, JSON.stringify(data));
      } catch (e) {
        console.warn('Session storage write failed:', e);
      }
    }

    return data;
  },

  /**
   * Part 5: Submit an asynchronous analysis job
   */
  async createAnalysisJob(payload) {
    if (typeof FormData !== 'undefined' && payload instanceof FormData) {
      return await request('/api/v1/analyze/jobs/upload', {
        method: 'POST',
        body: payload,
      });
    }

    const body = typeof payload === 'string'
      ? { sourceCode: payload, contractName: 'Contract.sol' }
      : payload;

    return await request('/api/v1/analyze/jobs', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },


  /**
   * Part 5: Cancel an in-flight or queued analysis job
   */
  async cancelJob(jobId) {
    return await request(`/api/v1/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },

  /**
   * Part 5: Retrieve completed analysis result of a job
   */
  async getJobResult(jobId) {
    return await request(`/api/v1/jobs/${jobId}/result`);
  },

  /**
   * Part 5: Delete an analysis job record
   */
  async deleteJob(jobId) {
    return await request(`/api/v1/jobs/${jobId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Retrieve an audit result by analysisId from live backend or cache
   */
  async getAnalysis(analysisId) {
    if (memoryCache.has(analysisId)) {
      return memoryCache.get(analysisId);
    }

    try {
      const saved = sessionStorage.getItem(`audit_${analysisId}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        memoryCache.set(analysisId, parsed);
        return parsed;
      }
    } catch (e) {
      console.warn('Session storage read failed:', e);
    }

    try {
      const data = await request(`/api/v1/analyze/${analysisId}`);
      if (data?.analysisId) {
        memoryCache.set(data.analysisId, data);
      }
      return data;
    } catch {
      return null;
    }
  },

  /**
   * Retrieve audit history from persistent storage
   */
  async listHistory(query = '', riskLevel = 'All') {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (riskLevel && riskLevel !== 'All') params.append('risk_level', riskLevel);

    return await request(`/api/v1/analyses?${params.toString()}`);
  },

  /**
   * Phase 6: Interactive Context-Scoped AI Legal Assistant query
   */
  async chatWithAssistant(analysisId, message) {
    return await request(`/api/v1/analyze/${analysisId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },

  /**
   * Phase 7: Real report download (PDF or DOCX)
   */
  async downloadReport(analysisId, format = 'PDF', contractName = 'Contract') {
    const ext = format.toLowerCase() === 'docx' ? 'docx' : 'pdf';
    const endpoint = `/api/v1/reports/${analysisId}/${ext}`;
    const baseUrl = getApiBaseUrl();
    const url = baseUrl ? `${baseUrl}${endpoint}` : endpoint;

    let response;
    try {
      response = await fetch(url);
    } catch (err) {
      throw new Error(`Unable to reach the report download service. Please verify backend connectivity.`, { cause: err });
    }

    if (!response.ok) {
      throw new Error(`Report export failed with status ${response.status}. The analysis may have expired.`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `${contractName.replace(/\s+/g, '_')}_Legal_AI_Audit_Report.${ext}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();
  },

  /**
   * Delete an analysis permanently from database and session cache
   */
  async deleteAnalysis(analysisId) {
    memoryCache.delete(analysisId);
    try {
      sessionStorage.removeItem(`audit_${analysisId}`);
    } catch (e) {
      console.warn('Session storage delete failed:', e);
    }
    return await request(`/api/v1/analyze/${analysisId}`, { method: 'DELETE' });
  },


  /**
   * Phase 4: Download uploaded/stored Solidity contract source file
   */
  async downloadContractSource(analysisId, filename = 'Contract.sol') {
    const baseUrl = getApiBaseUrl();
    const endpoint = `/api/v1/analyze/${analysisId}/file`;
    const url = baseUrl ? `${baseUrl}${endpoint}` : endpoint;

    const response = await fetch(url, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to download contract file (status ${response.status}).`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename.endsWith('.sol') ? filename : `${filename}.sol`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();
  },

  /**
   * Phase 4: Retrieve stored files for current user
   */
  async listUserFiles(limit = 50) {
    return await request(`/api/v1/files?limit=${limit}`);
  },

  /**
   * User dashboard personal statistics
   */
  async getUserStats() {
    return await request('/api/v1/user/stats');
  },

  /**
   * Direct cache helper
   */
  cacheAnalysis(data) {
    if (data?.analysisId) {
      memoryCache.set(data.analysisId, data);
      try {
        sessionStorage.setItem(`audit_${data.analysisId}`, JSON.stringify(data));
      } catch (e) {
        console.warn('Session storage write failed:', e);
      }
    }
  },
};

export default api;
