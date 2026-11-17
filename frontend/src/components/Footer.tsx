import React from 'react';
import { Shield, Lock, Terminal, FileCode2 } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="relative mt-20 border-t border-purple-500/15 bg-[#030107]/95 backdrop-blur-xl text-purple-300/60 text-xs">
      {/* Subtle top laser glow line */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 max-w-4xl h-[1px] bg-laser-gradient" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand & Logo */}
          <div className="flex flex-col items-center md:items-start space-y-2 text-center md:text-left">
            <div className="flex items-center space-x-2.5">
              <div className="w-6 h-6 rounded-md overflow-hidden border border-fuchsia-500/40 bg-black shrink-0">
                <img src="/valicrypt-logo.jpg" alt="ValiCrypt" className="w-full h-full object-cover scale-110" />
              </div>
              <span className="font-heading font-extrabold text-white text-base tracking-tight">ValiCrypt</span>
              <span className="cyber-badge rounded-md text-[10px] py-0 px-2 font-mono">v1.0.0</span>
            </div>
            <p className="max-w-md text-xs text-purple-300/60 leading-relaxed">
              Zero-knowledge steganographic carrier storage. Military-grade RFC 9106 Argon2id key derivation &amp; authenticated AES-256-GCM encryption embedded into lossless image and video containers.
            </p>
          </div>

          {/* Standards & Protocol Badges */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            <span className="cyber-badge rounded-md font-mono text-[10px]">
              <Lock className="w-2.5 h-2.5 text-fuchsia-400" />
              AES-256-GCM
            </span>
            <span className="cyber-badge rounded-md font-mono text-[10px]">
              <Shield className="w-2.5 h-2.5 text-purple-400" />
              RFC 9106 Argon2id
            </span>
            <span className="cyber-badge rounded-md font-mono text-[10px]">
              <Terminal className="w-2.5 h-2.5 text-fuchsia-400" />
              ISO/IEC 14496-12
            </span>
            <span className="cyber-badge rounded-md font-mono text-[10px]">
              <FileCode2 className="w-2.5 h-2.5 text-purple-400" />
              NumPy Vector LSB
            </span>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-purple-500/10 flex flex-col sm:flex-row items-center justify-between text-[11px] text-purple-400/40 gap-2">
          <p>© 2026 ARK. All rights reserved.</p>
          <p className="font-mono">Zero Plaintext Exposure • Certified Lossless Bit Integrity</p>
        </div>
      </div>
    </footer>
  );
};
