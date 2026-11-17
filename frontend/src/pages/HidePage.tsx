import React, { useState, useEffect } from 'react';
import {
  Lock,
  FileArchive,
  FileText,
  Image as ImageIcon,
  Film,
  Download,
  CheckCircle2,
  AlertCircle,
  Calculator,
  ShieldCheck,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { Dropzone } from '../components/Dropzone';
import { PasswordInput } from '../components/PasswordInput';
import { CapacityIndicator } from '../components/CapacityIndicator';
import { AlertBanner } from '../components/AlertBanner';
import { JobStatusTracker } from '../components/JobStatusTracker';
import { api } from '../services/api';
import { CapacityResult, EncodeSyncResponse, JobRecord } from '../types';

export const HidePage: React.FC = () => {
  const [carrierFile, setCarrierFile] = useState<File | null>(null);
  const [payloadType, setPayloadType] = useState<'text' | 'zip'>('text');
  const [textMessage, setTextMessage] = useState('');
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [password, setPassword] = useState('');

  // Capacity & calculations
  const [capacity, setCapacity] = useState<CapacityResult | null>(null);
  const [isCalculatingCapacity, setIsCalculatingCapacity] = useState(false);

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<EncodeSyncResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoDownloaded, setAutoDownloaded] = useState(false);

  const triggerAutoDownload = (url: string, filename: string) => {
    try {
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setAutoDownloaded(true);
    } catch (err) {
      console.warn('Auto download error:', err);
    }
  };

  // Compute payload size in bytes synchronously
  const payloadBytes = payloadType === 'text'
    ? new TextEncoder().encode(textMessage).length
    : (zipFile ? zipFile.size : 0);

  const isSufficient = capacity ? capacity.available_capacity_bytes >= payloadBytes : true;

  // Calculate carrier capacity ONCE when carrierFile changes (never re-fetch on text keystrokes)
  useEffect(() => {
    if (!carrierFile) {
      setCapacity(null);
      return;
    }

    let isMounted = true;
    const calculate = async () => {
      setIsCalculatingCapacity(true);
      try {
        const res = await api.checkCapacity(carrierFile, 0);
        if (isMounted) setCapacity(res);
      } catch (err: any) {
        console.warn('Capacity calculation error:', err);
      } finally {
        if (isMounted) setIsCalculatingCapacity(false);
      }
    };

    calculate();
    return () => {
      isMounted = false;
    };
  }, [carrierFile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!carrierFile) {
      setError('Please select a carrier image or video.');
      return;
    }
    if (!password) {
      setError('Please enter a secure password.');
      return;
    }
    if (payloadType === 'text' && !textMessage.trim()) {
      setError('Please enter a secret message to hide.');
      return;
    }
    if (payloadType === 'zip' && !zipFile) {
      setError('Please select a ZIP archive to hide.');
      return;
    }

    setError(null);
    setSyncResult(null);
    setActiveJobId(null);
    setAutoDownloaded(false);
    setIsSubmitting(true);

    try {
      if (payloadType === 'text') {
        const res = await api.encodeText(carrierFile, textMessage, password);
        if ('id' in res) {
          setActiveJobId(res.id);
        } else {
          setSyncResult(res);
          // Requirement 2: Automatic download upon completion
          if (res.download_url) {
            triggerAutoDownload(res.download_url, res.filename);
          }
        }
      } else {
        const res = await api.encodeZip(carrierFile, zipFile!, password);
        if ('id' in res) {
          setActiveJobId(res.id);
        } else {
          setSyncResult(res);
          // Requirement 2: Automatic download upon completion
          if (res.download_url) {
            triggerAutoDownload(res.download_url, res.filename);
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to embed payload into carrier.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 relative">
      {/* Page Header */}
      <div className="space-y-3 text-center sm:text-left">
        <div className="cyber-badge rounded-md">
          <span>&lt; Workflow A &gt;</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
          Hide Secret Data
        </h1>
        <p className="text-xs sm:text-sm text-purple-200/70 max-w-2xl leading-relaxed">
          Encrypt your text message or ZIP archive with authenticated AES-256-GCM and embed it losslessly inside an image or video carrier. Encoded files are automatically downloaded upon verification.
        </p>
      </div>

      {error && (
        <AlertBanner
          type="error"
          title="Operation Blocked"
          message={error}
          onClose={() => setError(null)}
        />
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Carrier Media Selection */}
        <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
          <div className="flex items-center space-x-3">
            <span className="w-7 h-7 rounded-lg bg-purple-900 border border-purple-500/40 text-purple-200 text-xs flex items-center justify-center font-bold">
              1
            </span>
            <h2 className="font-heading font-bold text-base text-white">Select Carrier Media</h2>
          </div>

          <Dropzone
            label="Carrier Media File (Image or Video)"
            sublabel="Supported: PNG, BMP, TIFF (Lossless Images) or MP4, MKV, MOV (Video Containers)"
            accept="image/png,image/bmp,image/tiff,video/mp4,video/x-matroska,video/quicktime,.png,.bmp,.tiff,.mp4,.mkv,.mov"
            fileType="any"
            selectedFile={carrierFile}
            onFileSelect={(file) => {
              setCarrierFile(file);
              setSyncResult(null);
              setActiveJobId(null);
            }}
          />

          {carrierFile && (
            <CapacityIndicator
              capacity={capacity}
              payloadBytes={payloadBytes}
              loading={isCalculatingCapacity}
            />
          )}
        </div>

        {/* Step 2: Payload Selection */}
        <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <span className="w-7 h-7 rounded-lg bg-purple-900 border border-purple-500/40 text-purple-200 text-xs flex items-center justify-center font-bold">
                2
              </span>
              <h2 className="font-heading font-bold text-base text-white">Select Secret Payload</h2>
            </div>

            {/* Mode Toggle Buttons (Cyber rounded-xl) */}
            <div className="flex rounded-xl bg-[#0d061c]/90 p-1 space-x-1.5 border border-purple-500/25 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setPayloadType('text')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  payloadType === 'text'
                    ? 'bg-gradient-to-r from-purple-700 to-fuchsia-700 text-white shadow-[0_0_15px_rgba(217,70,239,0.4)] border border-fuchsia-400/40'
                    : 'text-purple-300/60 hover:text-white border border-transparent'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Text Message</span>
              </button>

              <button
                type="button"
                onClick={() => setPayloadType('zip')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  payloadType === 'zip'
                    ? 'bg-gradient-to-r from-purple-700 to-fuchsia-700 text-white shadow-[0_0_15px_rgba(217,70,239,0.4)] border border-fuchsia-400/40'
                    : 'text-purple-300/60 hover:text-white border border-transparent'
                }`}
              >
                <FileArchive className="w-3.5 h-3.5" />
                <span>ZIP Archive</span>
              </button>
            </div>
          </div>

          {payloadType === 'text' ? (
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-purple-200">
                Secret Message (Unicode, Multilingual, Emojis)
              </label>
              <textarea
                value={textMessage}
                onChange={(e) => setTextMessage(e.target.value)}
                placeholder="Enter confidential message here... Supports English, Malayalam (രഹസ്യം), Hindi (गोपनीय), symbols & emojis 🔐"
                rows={5}
                className="w-full bg-[#0d061c]/80 border border-purple-500/25 focus:border-fuchsia-400 focus:ring-1 focus:ring-fuchsia-400/50 text-white rounded-xl p-4 text-xs sm:text-sm font-mono placeholder:text-purple-400/30 outline-none shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)] leading-relaxed"
              />
              <div className="flex justify-between text-[11px] text-purple-400/60 font-mono tabular-nums">
                <span>{textMessage.length} characters</span>
                <span>{payloadBytes} bytes (UTF-8 encoded)</span>
              </div>
            </div>
          ) : (
            <Dropzone
              label="Confidential ZIP Archive"
              sublabel="ZIP file containing sensitive folders/documents (Zip Slip & decompression bomb protected)"
              accept=".zip,application/zip,application/x-zip-compressed"
              fileType="zip"
              selectedFile={zipFile}
              onFileSelect={setZipFile}
            />
          )}
        </div>

        {/* Step 3: Password */}
        <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
          <div className="flex items-center space-x-3">
            <span className="w-7 h-7 rounded-lg bg-purple-900 border border-purple-500/40 text-purple-200 text-xs flex items-center justify-center font-bold">
              3
            </span>
            <h2 className="font-heading font-bold text-base text-white">Passphrase Authentication</h2>
          </div>

          <PasswordInput
            value={password}
            onChange={setPassword}
            placeholder="Choose a strong password for Argon2id key derivation..."
          />
        </div>

        {/* Action Button: Cyber Rounded-xl (Changed from capsule) */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isSubmitting || !isSufficient}
            className="w-full py-4 rounded-xl text-sm font-semibold tracking-wide text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] hover:shadow-[0_0_35px_rgba(217,70,239,0.7)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2.5 border border-fuchsia-400/40 hover:scale-[1.01]"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Deriving Key &amp; Embedding Secret...</span>
              </>
            ) : (
              <>
                <Lock className="w-4 h-4" />
                <span>Encrypt &amp; Embed Secret Payload</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Auto-Download Notification Banner */}
      {autoDownloaded && (
        <AlertBanner
          type="success"
          title="Auto-Download Initiated"
          message="Your encrypted carrier was validated and automatically saved to your browser downloads."
          onClose={() => setAutoDownloaded(false)}
        />
      )}

      {/* Synchronous Success Result Card */}
      {syncResult && (
        <div className="glass-card-featured rounded-2xl p-6 sm:p-8 space-y-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 laser-beam" />

          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(217,70,239,0.4)]">
              <CheckCircle2 className="w-6 h-6 text-fuchsia-400" />
            </div>
            <div>
              <h3 className="font-heading font-extrabold text-lg text-white">
                Carrier Embedding Verified &amp; Auto-Downloaded!
              </h3>
              <p className="text-xs text-purple-200/70">
                Data was encrypted with AES-256-GCM and embedded losslessly.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">CARRIER FORMAT</span>
              <span className="font-bold text-white uppercase">{syncResult.carrier_type}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">PAYLOAD TYPE</span>
              <span className="font-bold text-white uppercase">{syncResult.payload_type}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">OUTPUT SIZE</span>
              <span className="font-bold text-white">{(syncResult.output_size_bytes / 1024).toFixed(1)} KB</span>
            </div>
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">SHA-256</span>
              <span className="font-bold text-fuchsia-300 truncate block">{syncResult.sha256_checksum.slice(0, 10)}...</span>
            </div>
          </div>

          <a
            href={syncResult.download_url}
            download={syncResult.filename}
            className="w-full flex items-center justify-center space-x-2 py-3.5 px-6 rounded-xl text-xs sm:text-sm font-semibold tracking-wide text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all hover:scale-[1.01] border border-fuchsia-400/40"
          >
            <Download className="w-4 h-4" />
            <span>Re-download Carrier ({syncResult.filename})</span>
          </a>
        </div>
      )}

      {/* Asynchronous Background Job Tracker */}
      {activeJobId && (
        <JobStatusTracker
          jobId={activeJobId}
          onCompleted={(job) => {
            if (job.download_url) {
              triggerAutoDownload(job.download_url, job.filename || 'valicrypt_carrier');
            }
          }}
        />
      )}
    </div>
  );
};
