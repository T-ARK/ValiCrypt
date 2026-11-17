import React from 'react';
import { Database, CheckCircle2, AlertOctagon } from 'lucide-react';
import { CapacityResult } from '../types';

interface CapacityIndicatorProps {
  capacity: CapacityResult | null;
  payloadBytes: number;
  loading?: boolean;
}

export const CapacityIndicator: React.FC<CapacityIndicatorProps> = ({
  capacity,
  payloadBytes,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="p-5 rounded-2xl glass-panel animate-pulse flex items-center space-x-3 min-h-[110px]">
        <Database className="w-5 h-5 text-fuchsia-400 animate-spin" />
        <span className="text-xs font-mono text-purple-300">Calculating carrier payload capacity &amp; bits...</span>
      </div>
    );
  }

  if (!capacity) return null;

  const available = capacity.available_capacity_bytes;
  const isSufficient = available >= payloadBytes;
  const percentage = available > 0 ? Math.min(100, Math.round((payloadBytes / available) * 100)) : 0;

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className={`p-5 rounded-2xl border transition-all min-h-[110px] flex flex-col justify-between ${
      isSufficient
        ? 'glass-panel'
        : 'bg-rose-950/20 border-rose-500/40 shadow-[0_0_20px_rgba(244,63,94,0.15)]'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Database className={`w-4 h-4 ${isSufficient ? 'text-fuchsia-400' : 'text-rose-400'}`} />
          <span className="text-xs font-semibold uppercase tracking-wider text-purple-100">
            Carrier Steganographic Capacity
          </span>
        </div>
        <div className="flex items-center space-x-1.5 shrink-0">
          {isSufficient ? (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-purple-950/80 text-fuchsia-300 border border-purple-500/30 flex items-center space-x-1 shadow-[0_0_10px_rgba(217,70,239,0.2)]">
              <CheckCircle2 className="w-3.5 h-3.5 text-fuchsia-400" />
              <span>✓ Sufficient Capacity</span>
            </span>
          ) : (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-rose-950/80 text-rose-300 border border-rose-500/40 flex items-center space-x-1 shadow-[0_0_10px_rgba(244,63,94,0.3)]">
              <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
              <span>✗ Insufficient Capacity</span>
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar with Neon Violet Glow */}
      <div className="w-full bg-purple-950/60 h-2 rounded-md overflow-hidden my-2.5 border border-purple-500/20">
        <div
          className={`h-full transition-all duration-300 rounded-md ${
            isSufficient
              ? 'bg-gradient-to-r from-purple-500 via-fuchsia-500 to-purple-400 shadow-[0_0_12px_rgba(217,70,239,0.7)]'
              : 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.8)]'
          }`}
          style={{ width: `${Math.max(2, percentage)}%` }}
        />
      </div>

      {/* Tabular stable grid with no layout shift */}
      <div className="grid grid-cols-3 gap-2 text-xs font-mono text-purple-300/70 mt-1 tabular-nums">
        <span className="truncate">Payload: <strong className="text-white font-mono">{formatBytes(payloadBytes)}</strong></span>
        <span className="text-center truncate">Allocated: <strong className={isSufficient ? "text-fuchsia-300 font-mono" : "text-rose-400 font-mono"}>{percentage}%</strong></span>
        <span className="text-right truncate">Max: <strong className="text-white font-mono">{capacity.available_capacity_human}</strong></span>
      </div>

      {!isSufficient && (
        <p className="text-xs text-rose-300 mt-2.5 bg-rose-950/40 p-2.5 rounded-lg border border-rose-800/50">
          The selected payload exceeds available carrier capacity. Please choose a larger image/video or reduce the ZIP archive size.
        </p>
      )}
    </div>
  );
};
