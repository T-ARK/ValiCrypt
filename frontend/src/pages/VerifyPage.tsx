import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Search,
  FileCheck,
  Info,
  RefreshCw,
  AlertOctagon,
  FileCode,
  Sparkles,
} from 'lucide-react';
import { Dropzone } from '../components/Dropzone';
import { AlertBanner } from '../components/AlertBanner';
import { api } from '../services/api';
import { VerifyResponse } from '../types';

export const VerifyPage: React.FC = () => {
  const [carrierFile, setCarrierFile] = useState<File | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!carrierFile) {
      setError('Please select a carrier image or video.');
      return;
    }

    setError(null);
    setResult(null);
    setIsVerifying(true);

    try {
      const res = await api.verify(carrierFile);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Carrier forensic analysis failed.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 relative">
      {/* Header */}
      <div className="space-y-3 text-center sm:text-left">
        <div className="cyber-badge rounded-md">
          <span>&lt; Carrier Forensics &gt;</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
          Verify Media Integrity
        </h1>
        <p className="text-xs sm:text-sm text-purple-200/70 max-w-2xl leading-relaxed">
          Forensically inspect carrier headers, detect ValiCrypt structural preambles, and assess available bit capacity without exposing passwords.
        </p>
      </div>

      {error && (
        <AlertBanner
          type="error"
          title="Analysis Blocked"
          message={error}
          onClose={() => setError(null)}
        />
      )}

      <form onSubmit={handleVerify} className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
        <Dropzone
          label="Carrier Media to Forensically Analyze"
          sublabel="Accepts PNG, BMP, TIFF lossless images, or MP4, MKV, MOV video containers"
          accept="image/*,video/*,.png,.bmp,.mp4,.mkv,.mov"
          fileType="any"
          selectedFile={carrierFile}
          onFileSelect={(file) => {
            setCarrierFile(file);
            setResult(null);
          }}
        />

        <div className="pt-2">
          <button
            type="submit"
            disabled={isVerifying || !carrierFile}
            className="w-full py-4 rounded-xl text-sm font-semibold tracking-wide text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2.5 border border-fuchsia-400/40 hover:scale-[1.01]"
          >
            {isVerifying ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Scanning Media Atoms &amp; LSB Channels...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Execute Forensic Carrier Analysis</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Forensic Report Display */}
      {result && (
        <div className="glass-card-featured rounded-2xl p-6 sm:p-8 space-y-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 laser-beam" />

          <div className="flex items-center justify-between pb-3 border-b border-purple-500/20">
            <div className="flex items-center space-x-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
                  result.payload_present
                    ? 'bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-400/40 shadow-[0_0_15px_rgba(217,70,239,0.4)]'
                    : 'bg-purple-900/30 text-purple-300 border border-purple-500/30'
                }`}
              >
                {result.payload_present ? (
                  <ShieldCheck className="w-6 h-6 text-fuchsia-400" />
                ) : (
                  <Info className="w-6 h-6 text-purple-300" />
                )}
              </div>
              <div>
                <h3 className="font-heading font-extrabold text-lg text-white">
                  {result.payload_present
                    ? 'ValiCrypt Steganographic Payload Detected'
                    : 'Pristine Clean Carrier Media'}
                </h3>
                <p className="text-xs text-purple-200/70 font-mono">
                  Analysis Status: {result.integrity_status}
                </p>
              </div>
            </div>

            <span
              className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                result.payload_present
                  ? 'bg-purple-950/80 text-fuchsia-300 border-purple-500/30'
                  : 'bg-slate-900/80 text-purple-300 border-slate-700'
              }`}
            >
              {result.carrier_type}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 rounded-2xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">PAYLOAD TYPE</span>
              <span className="font-bold text-white">{result.payload_type || 'NONE'}</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">ENCRYPTION</span>
              <span className="font-bold text-white">{result.encryption_algorithm || 'NONE'}</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">KDF ALGORITHM</span>
              <span className="font-bold text-white">{result.kdf_algorithm || 'NONE'}</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0d061c]/80 border border-purple-500/20">
              <span className="text-purple-400/50 block text-[10px]">PAYLOAD SIZE</span>
              <span className="font-bold text-white">
                {result.payload_size_bytes ? `${(result.payload_size_bytes / 1024).toFixed(1)} KB` : 'N/A'}
              </span>
            </div>
          </div>

          {result.carrier_properties && Object.keys(result.carrier_properties).length > 0 && (
            <div className="p-4 rounded-2xl bg-[#0d061c]/90 border border-purple-500/25 space-y-2">
              <span className="text-xs font-mono font-bold text-purple-200 uppercase tracking-wider block">
                Technical Forensic Properties
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono text-purple-200/80">
                {Object.entries(result.carrier_properties).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-purple-500/10 pb-1">
                    <span className="text-purple-400/60">{k}:</span>
                    <span className="text-white font-semibold">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
