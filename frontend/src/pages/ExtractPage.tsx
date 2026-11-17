import React, { useState } from 'react';
import {
  Unlock,
  CheckCircle2,
  FileArchive,
  FileText,
  Download,
  Copy,
  Check,
  Search,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import { Dropzone } from '../components/Dropzone';
import { PasswordInput } from '../components/PasswordInput';
import { AlertBanner } from '../components/AlertBanner';
import { api } from '../services/api';
import { DecodeResponse, VerifyResponse } from '../types';

export const ExtractPage: React.FC = () => {
  const [carrierFile, setCarrierFile] = useState<File | null>(null);
  const [password, setPassword] = useState('');

  // Detection / Non-auth verification info
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectionInfo, setDetectionInfo] = useState<VerifyResponse | null>(null);

  // Extraction state
  const [isExtracting, setIsExtracting] = useState(false);
  const [result, setResult] = useState<DecodeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoDownloaded, setAutoDownloaded] = useState(false);

  // Copy state
  const [hasCopied, setHasCopied] = useState(false);

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

  const handleDetect = async () => {
    if (!carrierFile) {
      setError('Please select a carrier image or video first.');
      return;
    }
    setError(null);
    setIsDetecting(true);
    try {
      const info = await api.verify(carrierFile);
      setDetectionInfo(info);
    } catch (err: any) {
      setError(err.message || 'Carrier inspection failed.');
    } finally {
      setIsDetecting(false);
    }
  };

  const handleExtract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!carrierFile) {
      setError('Please select a carrier media file.');
      return;
    }
    if (!password) {
      setError('Please enter the password to decrypt the payload.');
      return;
    }

    setError(null);
    setResult(null);
    setAutoDownloaded(false);
    setIsExtracting(true);

    try {
      const res = await api.decode(carrierFile, password);
      setResult(res);

      // Requirement 2: Auto download upon clicking Decrypt & Recover Payload
      if (res.payload_type === 'ZIP' && res.download_url) {
        triggerAutoDownload(res.download_url, res.filename || 'valicrypt_recovered_archive.zip');
      } else if (res.payload_type === 'TEXT' && res.text_content) {
        const blob = new Blob([res.text_content], { type: 'text/plain;charset=utf-8' });
        const blobUrl = URL.createObjectURL(blob);
        triggerAutoDownload(blobUrl, 'valicrypt_recovered_secret.txt');
        setTimeout(() => URL.revokeObjectURL(blobUrl), 15000);
      }
    } catch (err: any) {
      setError(err.message || 'Decryption failed. Please verify the password and carrier file.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleCopyText = () => {
    if (result?.text_content) {
      navigator.clipboard.writeText(result.text_content);
      setHasCopied(true);
      setTimeout(() => setHasCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 relative">
      {/* Header */}
      <div className="space-y-3 text-center sm:text-left">
        <div className="cyber-badge rounded-md">
          <span>&lt; Workflow B &gt;</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
          Extract Confidential Data
        </h1>
        <p className="text-xs sm:text-sm text-purple-200/70 max-w-2xl leading-relaxed">
          Inspect encoded carrier media, derive the encryption key safely using Argon2id, authenticate Galois tags, and recover your secret payload with automatic download.
        </p>
      </div>

      {error && (
        <AlertBanner
          type="error"
          title="Extraction Blocked"
          message={error}
          onClose={() => setError(null)}
        />
      )}

      {autoDownloaded && (
        <AlertBanner
          type="success"
          title="Auto-Download Initiated"
          message="Your recovered payload has been decrypted, verified, and automatically downloaded to your machine."
          onClose={() => setAutoDownloaded(false)}
        />
      )}

      {/* Carrier Selection */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
        <div className="flex items-center space-x-3">
          <span className="w-7 h-7 rounded-lg bg-purple-900 border border-purple-500/40 text-purple-200 text-xs flex items-center justify-center font-bold">
            1
          </span>
          <h2 className="font-heading font-bold text-base text-white">Select Carrier Media</h2>
        </div>

        <Dropzone
          label="Encoded Carrier File (Image or Video)"
          sublabel="Drop an image (PNG, BMP, TIFF) or video (MP4, MKV, MOV) containing hidden ValiCrypt data"
          accept="image/*,video/*,.png,.bmp,.mp4,.mkv,.mov"
          fileType="any"
          selectedFile={carrierFile}
          onFileSelect={(file) => {
            setCarrierFile(file);
            setDetectionInfo(null);
            setResult(null);
          }}
        />

        {carrierFile && (
          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={handleDetect}
              disabled={isDetecting}
              className="px-5 py-2.5 rounded-xl bg-purple-950/60 hover:bg-purple-900/80 text-fuchsia-300 border border-purple-500/30 text-xs font-semibold flex items-center space-x-2 transition-all hover:scale-102"
            >
              {isDetecting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Scanning Carrier Bits...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>Detect Stego Envelope</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Technical detection info banner */}
        {detectionInfo && (
          <div className={`p-5 rounded-2xl border text-xs font-mono space-y-3 ${
            detectionInfo.payload_present
              ? 'bg-[#120826]/90 border-fuchsia-400/40 text-purple-200 shadow-[0_0_20px_rgba(217,70,239,0.15)]'
              : 'bg-[#0d061c]/80 border-purple-500/20 text-purple-300/50'
          }`}>
            <div className="flex items-center justify-between font-bold text-sm">
              <span className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-fuchsia-400" />
                <span>Payload Present: {detectionInfo.payload_present ? 'CONFIRMED' : 'NOT DETECTED'}</span>
              </span>
              <span className="text-[11px] font-normal px-2.5 py-0.5 rounded bg-purple-950/80 border border-purple-500/30">
                {detectionInfo.integrity_status}
              </span>
            </div>

            {detectionInfo.payload_present && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-purple-500/20 text-xs">
                <div>
                  <span className="text-purple-400/50 block text-[10px]">PAYLOAD TYPE</span>
                  <span className="text-white font-bold">{detectionInfo.payload_type}</span>
                </div>
                <div>
                  <span className="text-purple-400/50 block text-[10px]">ENCRYPTION</span>
                  <span className="text-white">{detectionInfo.encryption_algorithm}</span>
                </div>
                <div>
                  <span className="text-purple-400/50 block text-[10px]">KDF ALGORITHM</span>
                  <span className="text-white">{detectionInfo.kdf_algorithm}</span>
                </div>
                <div>
                  <span className="text-purple-400/50 block text-[10px]">PAYLOAD SIZE</span>
                  <span className="text-white font-bold">
                    {detectionInfo.payload_size_bytes
                      ? `${(detectionInfo.payload_size_bytes / 1024).toFixed(1)} KB`
                      : 'N/A'}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Password & Extract Action */}
      <form onSubmit={handleExtract} className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
        <div className="flex items-center space-x-3">
          <span className="w-7 h-7 rounded-lg bg-purple-900 border border-purple-500/40 text-purple-200 text-xs flex items-center justify-center font-bold">
            2
          </span>
          <h2 className="font-heading font-bold text-base text-white">Authentication Passphrase</h2>
        </div>

        <PasswordInput
          value={password}
          onChange={setPassword}
          label="Decryption Passphrase"
          placeholder="Enter the passphrase used when embedding the payload..."
          showStrength={false}
        />

        <div className="pt-2">
          <button
            type="submit"
            disabled={isExtracting || !carrierFile || !password}
            className="w-full py-4 rounded-xl text-sm font-semibold tracking-wide text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2.5 border border-fuchsia-400/40 hover:scale-[1.01]"
          >
            {isExtracting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Deriving Key &amp; Decrypting GCM Payload...</span>
              </>
            ) : (
              <>
                <Unlock className="w-4 h-4" />
                <span>Decrypt &amp; Recover Payload</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Recovered Content Display */}
      {result && (
        <div className="glass-card-featured rounded-2xl p-6 sm:p-8 space-y-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 laser-beam" />

          <div className="flex items-center justify-between pb-3 border-b border-purple-500/20">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(217,70,239,0.4)]">
                <CheckCircle2 className="w-6 h-6 text-fuchsia-400" />
              </div>
              <div>
                <h3 className="font-heading font-extrabold text-lg text-white">
                  Payload Successfully Decrypted &amp; Auto-Downloaded!
                </h3>
                <p className="text-xs text-purple-200/70 font-mono">
                  AES-256-GCM tag validated • SHA-256 integrity confirmed
                </p>
              </div>
            </div>

            <span className="px-3.5 py-1 rounded-lg text-xs font-mono font-bold bg-purple-950/80 text-fuchsia-300 border border-purple-500/30">
              {result.payload_type}
            </span>
          </div>

          {result.payload_type === 'TEXT' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-purple-200">
                  Recovered Plaintext Message (Saved to Downloads)
                </label>
                <button
                  onClick={handleCopyText}
                  className="px-4 py-1.5 rounded-lg bg-purple-950/60 hover:bg-purple-900 border border-purple-500/30 text-purple-200 text-xs font-medium flex items-center space-x-1.5 transition-all"
                >
                  {hasCopied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-fuchsia-400" />
                      <span className="text-fuchsia-300">Copied to Clipboard!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Message</span>
                    </>
                  )}
                </button>
              </div>

              <div className="p-4 rounded-xl bg-[#0d061c]/90 border border-purple-500/25 max-h-80 overflow-y-auto">
                <pre className="font-mono text-sm text-purple-100 whitespace-pre-wrap break-all leading-relaxed">
                  {result.text_content}
                </pre>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-5 rounded-xl bg-[#0d061c]/90 border border-purple-500/25 flex items-center space-x-3">
                <FileArchive className="w-8 h-8 text-fuchsia-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-bold text-white truncate">{result.filename}</h4>
                  <p className="text-xs text-purple-300/60 font-mono">
                    Size: {result.file_size_bytes ? `${(result.file_size_bytes / 1024).toFixed(1)} KB` : 'Archive Ready'} • Path Traversal Protected
                  </p>
                </div>
              </div>

              {result.download_url && (
                <a
                  href={result.download_url}
                  download={result.filename}
                  className="w-full flex items-center justify-center space-x-2 py-3.5 px-6 rounded-xl text-xs sm:text-sm font-semibold tracking-wide text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all hover:scale-[1.01] border border-fuchsia-400/40"
                >
                  <Download className="w-4 h-4" />
                  <span>Re-download Recovered ZIP Archive ({result.filename})</span>
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
