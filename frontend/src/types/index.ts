export type CarrierType = 'image' | 'video';
export type PayloadType = 'text' | 'zip';

export interface HealthInfo {
  status: string;
  service: string;
  version: string;
  environment: string;
  capabilities: {
    image_steganography: boolean;
    video_steganography: boolean;
    ffmpeg_path: string;
    ffprobe_path: string;
    encryption: string;
    kdf: string;
    max_upload_size_mb: number;
    max_payload_size_mb: number;
  };
}

export interface CapacityResult {
  carrier_type: 'IMAGE' | 'VIDEO';
  carrier_size_bytes: number;
  available_capacity_bytes: number;
  available_capacity_human: string;
  sufficient: boolean;
  carrier_info: Record<string, any>;
}

export interface EncodeSyncResponse {
  success: boolean;
  job_id: string;
  download_url: string;
  filename: string;
  mime_type: string;
  carrier_type: string;
  payload_type: string;
  output_size_bytes: number;
  sha256_checksum: string;
}

export interface DecodeResponse {
  success: boolean;
  payload_type: 'TEXT' | 'ZIP' | 'BINARY';
  text_content?: string;
  download_url?: string;
  filename?: string;
  file_size_bytes?: number;
  sha256_checksum: string;
  metadata?: Record<string, any>;
}

export interface VerifyResponse {
  carrier_type: 'IMAGE' | 'VIDEO';
  media_format: string;
  mediavault_version?: number;
  payload_present: boolean;
  payload_type?: string;
  encryption_algorithm?: string;
  kdf_algorithm?: string;
  payload_size_bytes?: number;
  integrity_status: 'VALID' | 'NOT_DETECTED' | 'CORRUPTED';
  carrier_properties: Record<string, any>;
  disclaimer: string;
}

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'VERIFYING' | 'COMPLETED' | 'FAILED';

export interface JobRecord {
  id: string;
  status: JobStatus;
  operation: string;
  carrier_type: string;
  payload_type?: string;
  carrier_size: number;
  payload_size?: number;
  progress: number;
  error_code?: string;
  error_message?: string;
  download_url?: string;
  filename?: string;
  mime_type?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}
