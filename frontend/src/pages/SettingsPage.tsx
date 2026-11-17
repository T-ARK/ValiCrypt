import React from 'react';
import { Shield } from 'lucide-react';
import { HealthInfo } from '../types';

interface SettingsPageProps {
  health: HealthInfo | null;
}

export const SettingsPage: React.FC<SettingsPageProps> = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8 relative">
      <div className="space-y-3 text-center sm:text-left">
        <div className="cyber-badge rounded-md">
          <span>&lt; Config &gt;</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
          System &amp; Security Config
        </h1>
        <p className="text-xs sm:text-sm text-purple-200/70 max-w-xl leading-relaxed">
          Cryptographic enforcement parameters, memory-hard derivation thresholds, and envelope security standards.
        </p>
      </div>

      {/* Cryptographic Profile Card */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl relative overflow-hidden">
        <div className="flex items-center space-x-3 pb-3 border-b border-purple-500/15">
          <Shield className="w-5 h-5 text-fuchsia-400" />
          <h2 className="font-heading font-bold text-base text-white">Cryptographic Standards</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-[#0d061c]/80 border border-purple-500/20 space-y-1">
            <span className="text-purple-400/50 block text-[10px]">KDF ALGORITHM</span>
            <span className="text-fuchsia-300 text-sm font-bold">Argon2id (RFC 9106)</span>
            <p className="text-[11px] text-purple-200/70 mt-1">
              Time Cost: 2 iterations • Memory Cost: 65,536 KiB (64 MiB) • Parallelism: 4 lanes
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#0d061c]/80 border border-purple-500/20 space-y-1">
            <span className="text-purple-400/50 block text-[10px]">SYMMETRIC CIPHER</span>
            <span className="text-fuchsia-300 text-sm font-bold">AES-256-GCM (NIST SP 800-38D)</span>
            <p className="text-[11px] text-purple-200/70 mt-1">
              Key: 256 bits • Nonce: 96 bits fresh random • GMAC Tag: 128 bits authenticated
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#0d061c]/80 border border-purple-500/20 space-y-1">
            <span className="text-purple-400/50 block text-[10px]">AUTHENTICATED DATA (AAD)</span>
            <span className="text-white text-sm font-bold">92-Byte Binary Header</span>
            <p className="text-[11px] text-purple-200/70 mt-1">
              Binds salt, algorithm ID, and payload length into GCM authentication tag.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#0d061c]/80 border border-purple-500/20 space-y-1">
            <span className="text-purple-400/50 block text-[10px]">PAYLOAD CHECKSUM</span>
            <span className="text-white text-sm font-bold">SHA-256 Digest</span>
            <p className="text-[11px] text-purple-200/70 mt-1">
              Embedded in envelope; verified post-decryption before any disk or memory release.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
