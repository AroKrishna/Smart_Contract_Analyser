/**
 * frontend/src/services/api.js
 * Real API client connecting the React frontend to the FastAPI backend service.
 */

const isDev = Boolean(import.meta.env.DEV);
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const DIRECT_BACKEND_URL = isDev ? 'http://127.0.0.1:8000' : '';

// In-memory session cache for fast tab-switching
const memoryCache = new Map();

/**
 * Helper to execute HTTP requests with automatic fallback to direct backend URL in local development mode.
 */
async function fetchWithFallback(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const primaryUrl = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(primaryUrl, { credentials: 'omit', ...options, headers });
    return response;
  } catch (primaryErr) {
    if (isDev && !API_BASE_URL && DIRECT_BACKEND_URL) {
      const fallbackUrl = `${DIRECT_BACKEND_URL}${endpoint}`;
      try {
        const fallbackResponse = await fetch(fallbackUrl, { ...options, headers });
        return fallbackResponse;
      } catch (fallbackErr) {
        throw new Error(
          `Unable to connect to the analysis service at ${DIRECT_BACKEND_URL}. ` +
          `Please ensure the FastAPI backend is running via: uvicorn analysis.api:app --reload --port 8000`,
          { cause: fallbackErr }
        );
      }
    }
    throw new Error(
      'Unable to connect to the Smart Contract Analyser backend service. Please check your network connection or verify service status.',
      { cause: primaryErr }
    );
  }
}

export const api = {
  /**
   * Health check endpoint
   */
  async checkHealth() {
    try {
      const res = await fetchWithFallback('/api/v1/health');
      if (!res.ok) {
        throw new Error(`Health check returned status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.warn('Backend health check failed:', err.message);
      return { status: 'offline', error: err.message };
    }
  },

  /**
   * Phase 1: Initiate asynchronous Legal-BERT analysis job with real progress tracking
   */
  async startAnalysisJob(sourceCode, contractName = 'Contract.sol', description = '') {
    const response = await fetchWithFallback('/api/v1/analyze/jobs', {
      method: 'POST',
      body: JSON.stringify({
        sourceCode,
        contractName,
        description,
      }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let errorMessage = 'Failed to initiate analysis job.';
      if (data?.detail) {
        errorMessage = typeof data.detail === 'object' ? (data.detail.message || JSON.stringify(data.detail)) : data.detail;
      } else if (response.status === 413) {
        errorMessage = 'Source code exceeds maximum permitted payload size of 2MB.';
      } else if (response.status === 400) {
        errorMessage = 'Invalid or empty Solidity source submitted.';
      } else if (response.status === 422) {
        errorMessage = 'Unsupported or non-Solidity source submitted.';
      }
      const error = new Error(errorMessage);
      error.status = response.status;
      error.detail = data?.detail;
      throw error;
    }

    return data;
  },

  /**
   * Phase 1: Upload .sol file directly via multipart form data
   */
  async uploadContractFile(file, contractName = '', description = '') {
    const formData = new FormData();
    formData.append('file', file);
    if (contractName) formData.append('contract_name', contractName);
    if (description) formData.append('description', description);

    const primaryUrl = `${API_BASE_URL || DIRECT_BACKEND_URL}/api/v1/analyze/upload`;
    const response = await fetch(primaryUrl, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let errorMessage = 'File upload failed.';
      if (data?.detail) {
        errorMessage = typeof data.detail === 'object' ? (data.detail.message || JSON.stringify(data.detail)) : data.detail;
      } else if (response.status === 413) {
        errorMessage = 'Uploaded file exceeds 2MB limit.';
      } else if (response.status === 400) {
        errorMessage = 'Invalid file type. Only Solidity .sol files are supported.';
      }
      const error = new Error(errorMessage);
      error.status = response.status;
      error.detail = data?.detail;
      throw error;
    }

    return data;
  },

  /**
   * Phase 1: Poll real analysis job status and progress
   */
  async getJobStatus(jobId) {
    const response = await fetchWithFallback(`/api/v1/jobs/${jobId}`);
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new Error(data?.detail?.message || `Job status check failed (${response.status})`);
    }
    const data = await response.json();
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
      await fetchWithFallback(`/api/v1/analyze/${analysisId}/discard`, {
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
    const response = await fetchWithFallback('/api/v1/analyze', {
      method: 'POST',
      body: JSON.stringify({
        sourceCode,
        contractName,
        description,
      }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let errorMessage = 'Analysis failed.';
      if (data?.detail) {
        if (typeof data.detail === 'object') {
          errorMessage = data.detail.message || JSON.stringify(data.detail);
        } else {
          errorMessage = data.detail;
        }
      } else if (response.status === 413) {
        errorMessage = 'Source code exceeds maximum permitted payload size of 2MB.';
      } else if (response.status === 400) {
        errorMessage = 'Invalid or empty Solidity source submitted.';
      } else if (response.status === 422) {
        errorMessage = 'Unsupported or non-Solidity source submitted.';
      } else if (response.status >= 500) {
        errorMessage = 'Backend analysis service is currently unavailable. Please ensure FastAPI is running on port 8000.';
      }

      const error = new Error(errorMessage);
      error.status = response.status;
      error.detail = data?.detail;
      throw error;
    }

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

    const response = await fetchWithFallback(`/api/v1/analyze/${analysisId}`);
    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    if (data?.analysisId) {
      memoryCache.set(data.analysisId, data);
    }
    return data;
  },

  /**
   * Retrieve audit history from persistent storage
   */
  async listHistory(query = '', riskLevel = 'All') {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (riskLevel && riskLevel !== 'All') params.append('risk_level', riskLevel);

    const response = await fetchWithFallback(`/api/v1/analyses?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch history (status ${response.status})`);
    }
    return await response.json();
  },

  /**
   * Phase 6: Interactive Context-Scoped AI Legal Assistant query
   */
  async chatWithAssistant(analysisId, message) {
    const response = await fetchWithFallback(`/api/v1/analyze/${analysisId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => null);
      throw new Error(err?.detail?.message || 'Chat assistant query failed.');
    }
    return await response.json();
  },

  /**
   * Phase 7: Real report download (PDF or DOCX)
   */
  async downloadReport(analysisId, format = 'PDF', contractName = 'Contract') {
    const ext = format.toLowerCase() === 'docx' ? 'docx' : 'pdf';
    const endpoint = `/api/v1/reports/${analysisId}/${ext}`;

    const baseUrl = API_BASE_URL || (isDev ? DIRECT_BACKEND_URL : '');
    const url = `${baseUrl}${endpoint}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Report export failed with status ${response.status}`);
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
   * Phase 13: Admin Control Panel endpoints
   */
  async getAdminStats() {
    const res = await fetchWithFallback('/api/v1/admin/stats');
    if (!res.ok) throw new Error('Failed to load admin stats');
    return await res.json();
  },

  async getAdminUsers() {
    const res = await fetchWithFallback('/api/v1/admin/users');
    if (!res.ok) throw new Error('Failed to load admin users');
    return await res.json();
  },

  async getAdminModelStatus() {
    const res = await fetchWithFallback('/api/v1/admin/model-status');
    if (!res.ok) throw new Error('Failed to load model status');
    return await res.json();
  },

  /**
   * Phase 1 & 11: Auth methods
   */
  async login(email, password) {
    const res = await fetchWithFallback('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      throw new Error(data?.detail?.message || 'Invalid credentials');
    }
    return await res.json();
  },

  async register(email, password, fullName, organization) {
    const res = await fetchWithFallback('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, fullName, organization }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      throw new Error(data?.detail?.message || 'Registration failed');
    }
    return await res.json();
  },

  async getCurrentUser() {
    const res = await fetchWithFallback('/api/v1/auth/me');
    if (!res.ok) return null;
    return await res.json();
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
