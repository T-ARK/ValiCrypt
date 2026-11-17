import {
  CapacityResult,
  DecodeResponse,
  EncodeSyncResponse,
  HealthInfo,
  JobRecord,
  VerifyResponse,
} from '../types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  code: string;
  details: Record<string, any>;
  statusCode: number;

  constructor(message: string, code: string = 'UNKNOWN_ERROR', details: Record<string, any> = {}, statusCode: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
    this.statusCode = statusCode;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errBody: any = null;
    try {
      errBody = await res.json();
    } catch {
      // Non-JSON response
    }
    const code = errBody?.error?.code || `HTTP_${res.status}`;
    const msg = errBody?.error?.message || errBody?.detail || res.statusText || 'Request failed';
    const details = errBody?.error?.details || {};
    throw new ApiError(msg, code, details, res.status);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<HealthInfo> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthInfo>(res);
  },

  async checkCapacity(carrier: File, payloadSize: number = 0): Promise<CapacityResult> {
    const formData = new FormData();
    formData.append('carrier', carrier);
    formData.append('payload_size', payloadSize.toString());

    const res = await fetch(`${API_BASE}/capacity`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<CapacityResult>(res);
  },

  async encodeText(carrier: File, message: string, password: string): Promise<EncodeSyncResponse | JobRecord> {
    const formData = new FormData();
    formData.append('carrier', carrier);
    formData.append('message', message);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/encode/text`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<EncodeSyncResponse | JobRecord>(res);
  },

  async encodeZip(carrier: File, zipFile: File, password: string): Promise<EncodeSyncResponse | JobRecord> {
    const formData = new FormData();
    formData.append('carrier', carrier);
    formData.append('payload', zipFile);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/encode/zip`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<EncodeSyncResponse | JobRecord>(res);
  },

  async decode(carrier: File, password: string): Promise<DecodeResponse> {
    const formData = new FormData();
    formData.append('carrier', carrier);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/decode`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DecodeResponse>(res);
  },

  async verify(carrier: File): Promise<VerifyResponse> {
    const formData = new FormData();
    formData.append('carrier', carrier);

    const res = await fetch(`${API_BASE}/verify`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<VerifyResponse>(res);
  },

  async getJob(jobId: string): Promise<JobRecord> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    return handleResponse<JobRecord>(res);
  },

  async listJobs(): Promise<JobRecord[]> {
    const res = await fetch(`${API_BASE}/jobs`);
    return handleResponse<JobRecord[]>(res);
  },
};
