import React, { useState } from 'react';
import {
  Lock,
  Unlock,
  CheckCircle2,
  FileArchive,
  Film,
  Image as ImageIcon,
  Key,
  Shield,
  ArrowRight,
  Database,
  Cpu,
  Sparkles,
  Layers,
  Search,
  Eye,
  FileCheck,
  Zap,
  HelpCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { HealthInfo } from '../types';
import { GlyphLottery } from '../components/GlyphLottery';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
  health: HealthInfo | null;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate, health }) => {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const faqs = [
    {
      question: 'How does ValiCrypt hide encrypted payloads inside media files?',
      answer:
        'ValiCrypt uses two distinct carrier steganography engines: For lossless images (PNG, BMP, TIFF), it utilizes vectorized NumPy Least Significant Bit (LSB) embedding across RGB channels. For video files (MP4, MKV, MOV), it embeds payloads into ISO/IEC 14496-12 custom UUID atoms, ensuring 100% normal video playback while carrying authenticated ciphertext.',
    },
    {
      question: 'What cryptographic parameters protect payloads against brute force and tampering?',
      answer:
        'Every payload undergoes key derivation via Argon2id (RFC 9106) configured with 64 MiB memory cost, 2 iterations, and 4 parallel lanes to thwart GPU/ASIC attacks. Encryption is handled by AES-256 in Galois/Counter Mode (GCM) using a cryptographically secure random 96-bit nonce and a 92-byte binary header bound as Associated Authenticated Data (AAD) with a 16-byte GMAC tag.',
    },
    {
      question: 'Why are lossless carriers required for image steganography?',
      answer:
        'Lossy formats such as JPEG utilize Discrete Cosine Transform (DCT) and quantization tables that overwrite low-order bit planes during compression. By utilizing lossless carriers (PNG, BMP, TIFF), ValiCrypt guarantees bit-exact payload recovery without risk of data corruption.',
    },
    {
      question: 'Does ValiCrypt retain secrets, passwords, or carrier history?',
      answer:
        'No. ValiCrypt operates under a strict zero-knowledge architecture. Encryption keys exist only ephemerally in RAM during processing and are immediately zeroized. Temporary upload files are securely deleted after encoding/decoding, and only minimal non-sensitive operational telemetry is retained.',
    },
    {
      question: 'How do the instant auto-download workflows operate?',
      answer:
        'Upon clicking "Encrypt & Embed Secret Payload" (Workflow A) or "Decrypt & Recover Payload" (Workflow B), the server processes the carrier and generates a verified response. ValiCrypt immediately triggers a client-side browser download saving the file directly to your disk without requiring manual second-step confirmation.',
    },
  ];
  return (
    <div className="space-y-20 relative">
      {/* Top Ambient Dome Light */}
      <div className="ambient-dome" />
      <div className="celestial-light" />

      {/* ========================================================================= */}
      {/* 1. HERO SECTION WITH GLYPH LOTTERY HEADLINE & NEW LOGO ART */}
      {/* ========================================================================= */}
      <section className="relative z-10 pt-6 sm:pt-14 pb-6 text-center max-w-4xl mx-auto space-y-6">
        {/* Cyber Badge */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-purple-950/70 border border-fuchsia-500/30 backdrop-blur-md shadow-[0_0_15px_rgba(217,70,239,0.25)]">
          <Sparkles className="w-3.5 h-3.5 text-fuchsia-400" />
          <span className="text-xs font-mono font-semibold tracking-wider uppercase text-purple-200">
            ValiCrypt • Zero-Knowledge Steganographic Carrier Engine
          </span>
        </div>

        {/* GLYPH LOTTERY: Letters spin like slot reels and lock into headline */}
        <div className="py-2">
          <GlyphLottery
            text="PRECISION SECURITY FOR MODERN MEDIA"
            className="text-3xl sm:text-5xl md:text-6xl font-extrabold text-white leading-tight"
          />
        </div>

        {/* Subtitle */}
        <p className="text-sm sm:text-base text-purple-200/70 max-w-2xl mx-auto leading-relaxed font-normal">
          Harness authenticated AES-256-GCM encryption and carrier steganography. Hide encrypted ZIP archives and Unicode text inside lossless images and video containers with zero perceptual distortion and zero key exposure.
        </p>

        {/* Action Buttons: Sleek cyber rounded-xl buttons (not capsule pills) */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-3">
          <button
            onClick={() => onNavigate('hide')}
            className="flex items-center space-x-2.5 px-8 py-3.5 rounded-xl text-sm font-semibold tracking-wide text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] hover:shadow-[0_0_35px_rgba(217,70,239,0.7)] transition-all duration-300 hover:scale-105 active:scale-95 border border-fuchsia-400/40"
          >
            <Lock className="w-4 h-4 text-purple-200" />
            <span>Hide Payload</span>
          </button>

          <button
            onClick={() => onNavigate('extract')}
            className="flex items-center space-x-2.5 px-8 py-3.5 rounded-xl text-sm font-semibold tracking-wide text-purple-200 bg-[#120826]/80 hover:bg-[#1f0e42]/90 border border-purple-500/30 hover:border-fuchsia-400/60 backdrop-blur-md transition-all duration-300 hover:scale-105 active:scale-95 shadow-[0_0_15px_rgba(168,85,247,0.15)]"
          >
            <Unlock className="w-4 h-4 text-fuchsia-400" />
            <span>Extract &amp; Decrypt</span>
          </button>

          <button
            onClick={() => onNavigate('verify')}
            className="flex items-center space-x-2.5 px-8 py-3.5 rounded-xl text-sm font-semibold tracking-wide text-purple-300/80 bg-[#0d061c]/70 hover:bg-[#150a2e]/80 border border-purple-500/20 hover:border-purple-400/50 backdrop-blur-md transition-all duration-300"
          >
            <CheckCircle2 className="w-4 h-4 text-purple-400" />
            <span>Verify Media</span>
          </button>
        </div>

        {/* Subtle Brand/Protocol Trust Bar */}
        <div className="pt-8 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs text-purple-300/40 font-mono tracking-wider">
          <span>● RFC 9106 ARGON2ID</span>
          <span>● AES-256-GCM AAD</span>
          <span>● ISO/IEC 14496-12</span>
          <span>● FFMPEG LOSSLESS</span>
          <span>● NUMPY RGB-LSB</span>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 2. STATS BANNER */}
      {/* ========================================================================= */}
      <section className="relative z-10 glass-panel rounded-2xl p-6 sm:p-8 max-w-5xl mx-auto shadow-[0_10px_40px_rgba(0,0,0,0.6)]">
        <div className="grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-purple-500/15 text-center">
          <div className="p-4 sm:p-6 space-y-1">
            <div className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
              48+
            </div>
            <div className="text-[11px] font-mono tracking-widest text-purple-300/60 uppercase">
              Passing Test Suites
            </div>
          </div>

          <div className="p-4 sm:p-6 space-y-1">
            <div className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
              100%
            </div>
            <div className="text-[11px] font-mono tracking-widest text-purple-300/60 uppercase">
              Lossless Accuracy
            </div>
          </div>

          <div className="p-4 sm:p-6 space-y-1">
            <div className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
              256-Bit
            </div>
            <div className="text-[11px] font-mono tracking-widest text-purple-300/60 uppercase">
              Authenticated AES
            </div>
          </div>

          <div className="p-4 sm:p-6 space-y-1">
            <div className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
              0s
            </div>
            <div className="text-[11px] font-mono tracking-widest text-purple-300/60 uppercase">
              Key Memory Lifetime
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. SPLIT ARCHITECTURE PREVIEW */}
      {/* ========================================================================= */}
      <section className="relative z-10 max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
        {/* Left Side */}
        <div className="space-y-4">
          <div className="cyber-badge rounded-md">
            <span>&lt; Core Engine &gt;</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-heading font-bold text-white tracking-tight leading-tight">
            Next-Generation <br />
            Carrier Steganography
          </h2>

          <p className="text-sm sm:text-base text-purple-200/70 leading-relaxed">
            ValiCrypt combines memory-hard password derivation, authenticated Galois/Counter Mode encryption, and lossless container steganography to turn ordinary media into tamper-proof data vaults.
          </p>

          <div className="flex items-center space-x-3 pt-2">
            <div className="flex -space-x-2">
              <div className="w-8 h-8 rounded-lg bg-purple-700 border-2 border-[#05020c] flex items-center justify-center text-[10px] font-bold text-white">
                KDF
              </div>
              <div className="w-8 h-8 rounded-lg bg-fuchsia-600 border-2 border-[#05020c] flex items-center justify-center text-[10px] font-bold text-white">
                GCM
              </div>
              <div className="w-8 h-8 rounded-lg bg-cyan-600 border-2 border-[#05020c] flex items-center justify-center text-[10px] font-bold text-white">
                LSB
              </div>
            </div>
            <span className="text-xs text-purple-300/80 font-medium">
              Real-time auto-download on completion • Zero lingering history
            </span>
          </div>
        </div>

        {/* Right Side: Feature Preview Glass Card */}
        <div className="relative glass-panel rounded-2xl p-6 sm:p-8 space-y-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-laser-gradient" />

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-fuchsia-400" />
              <span className="font-heading font-bold text-white text-base">ValiCrypt Security Core</span>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
              RFC 9106
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/15 space-y-1">
              <span className="text-purple-300/50 block font-mono text-[10px]">KDF PARAMETERS</span>
              <p className="font-semibold text-white">64 MiB • 2 Iterations</p>
            </div>
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/15 space-y-1">
              <span className="text-purple-300/50 block font-mono text-[10px]">ENVELOPE FORMAT</span>
              <p className="font-semibold text-white">MV01 92-Byte Header</p>
            </div>
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/15 space-y-1">
              <span className="text-purple-300/50 block font-mono text-[10px]">IMAGE EMBEDDING</span>
              <p className="font-semibold text-white">NumPy RGB Lossless</p>
            </div>
            <div className="p-3 rounded-xl bg-[#0d061c]/80 border border-purple-500/15 space-y-1">
              <span className="text-purple-300/50 block font-mono text-[10px]">VIDEO CONTAINER</span>
              <p className="font-semibold text-white">ISO/IEC 14496-12 UUID</p>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-purple-500/15 text-xs text-purple-300/70">
            <span>Automated decode verification &amp; instant download</span>
            <CheckCircle2 className="w-4 h-4 text-fuchsia-400" />
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. WORKFLOW CARDS (Rounded-2xl cyber styling) */}
      {/* ========================================================================= */}
      <section className="relative z-10 max-w-6xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <div className="cyber-badge rounded-md">
            <span>&lt; Workflows &gt;</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
            Carrier Security Workflows
          </h2>
          <p className="text-sm text-purple-200/60 max-w-xl mx-auto">
            Lossless embedding and zero-knowledge extraction with automatic instant download.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 items-stretch">
          {/* Card 1: Workflow A */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-6 sm:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="inline-block px-2.5 py-1 rounded text-[11px] font-mono font-medium text-purple-300 bg-purple-950/60 border border-purple-500/30">
                Workflow A
              </div>
              <h3 className="text-xl font-heading font-bold text-white">Hide Payload</h3>
              <p className="text-xs text-purple-200/70 leading-relaxed">
                Embed confidential Unicode text or multi-file ZIP archives into image or video carriers with automatic capacity validation and instant download.
              </p>

              <div className="space-y-2 pt-2 text-xs text-purple-200/80">
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
                  <span>Lossless PNG, BMP, TIFF (RGB LSB)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
                  <span>MP4, MOV (UUID Atom) &amp; MKV Containers</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
                  <span>Auto-Download Encoded Carrier</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => onNavigate('hide')}
              className="w-full py-3 rounded-xl text-xs font-semibold text-purple-200 bg-purple-950/60 hover:bg-purple-900/80 border border-purple-500/30 hover:border-fuchsia-400 transition-all flex items-center justify-center space-x-2"
            >
              <span>Launch Hide Tool</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 2: Workflow B */}
          <div className="glass-card-featured rounded-2xl p-6 sm:p-8 flex flex-col justify-between space-y-6 relative overflow-hidden transform md:-translate-y-2">
            <div className="absolute top-0 left-0 right-0 laser-beam" />

            <div className="space-y-4">
              <div className="inline-block px-2.5 py-1 rounded text-[11px] font-mono font-semibold text-white bg-gradient-to-r from-purple-600 to-fuchsia-600 shadow-[0_0_12px_rgba(217,70,239,0.5)]">
                ★ Core Workflow B
              </div>
              <h3 className="text-xl font-heading font-extrabold text-white">
                Extract &amp; Decrypt
              </h3>
              <p className="text-xs text-purple-100/80 leading-relaxed">
                Detect embedded ValiCrypt payloads, derive keys in-memory via Argon2id, authenticate AAD tags, and automatically download recovered files.
              </p>

              <div className="space-y-2 pt-2 text-xs text-purple-100/90 font-medium">
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_6px_#fff]" />
                  <span>Automatic Carrier Detection &amp; Inspection</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_6px_#fff]" />
                  <span>Immediate Auto-Download of Recovered Payload</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_6px_#fff]" />
                  <span>Zero Lingering History (Up-to-Date Data Only)</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => onNavigate('extract')}
              className="w-full py-3.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all flex items-center justify-center space-x-2 hover:scale-102 border border-fuchsia-400/40"
            >
              <span>Launch Extract Tool</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 3: Verify Media */}
          <div className="glass-panel glass-panel-hover rounded-2xl p-6 sm:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="inline-block px-2.5 py-1 rounded text-[11px] font-mono font-medium text-purple-300 bg-purple-950/60 border border-purple-500/30">
                Forensics
              </div>
              <h3 className="text-xl font-heading font-bold text-white">Verify Media</h3>
              <p className="text-xs text-purple-200/70 leading-relaxed">
                Scan suspicious media files for hidden payloads, verify container structural integrity, and calculate steganographic capacity.
              </p>

              <div className="space-y-2 pt-2 text-xs text-purple-200/80">
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
                  <span>Bit-Exact Forensic Capacity Estimator</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
                  <span>Preamble &amp; Atom Structure Detection</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
                  <span>FFprobe Playback Characteristic Check</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => onNavigate('verify')}
              className="w-full py-3 rounded-xl text-xs font-semibold text-purple-200 bg-purple-950/60 hover:bg-purple-900/80 border border-purple-500/30 hover:border-fuchsia-400 transition-all flex items-center justify-center space-x-2"
            >
              <span>Verify Media Carrier</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. ARCHITECTURAL FAQ & GEO KNOWLEDGE SECTION */}
      {/* ========================================================================= */}
      <section className="relative z-10 max-w-4xl mx-auto space-y-8 pt-4 pb-12">
        <div className="text-center space-y-2">
          <div className="cyber-badge rounded-md">
            <span>&lt; Knowledge Base &gt;</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-heading font-extrabold text-white tracking-tight">
            Cryptographic Architecture &amp; FAQ
          </h2>
          <p className="text-xs sm:text-sm text-purple-200/60 max-w-lg mx-auto">
            Deep dive into ValiCrypt's zero-knowledge security standards, container formats, and operational mechanisms.
          </p>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div
                key={idx}
                className={`rounded-2xl transition-all duration-300 border ${
                  isOpen
                    ? 'bg-[#120726]/90 border-fuchsia-500/40 shadow-[0_4px_25px_rgba(217,70,239,0.15)]'
                    : 'bg-[#0c051a]/70 border-purple-500/20 hover:border-purple-400/40'
                }`}
              >
                <button
                  type="button"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  className="w-full px-5 sm:px-6 py-4.5 flex items-center justify-between text-left space-x-4 cursor-pointer"
                  aria-expanded={isOpen}
                >
                  <span className="font-heading font-semibold text-sm sm:text-base text-white">
                    {faq.question}
                  </span>
                  <div className="shrink-0 p-1 rounded-lg bg-purple-900/40 text-purple-300">
                    {isOpen ? (
                      <ChevronUp className="w-4 h-4 text-fuchsia-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-purple-400" />
                    )}
                  </div>
                </button>

                {isOpen && (
                  <div className="px-5 sm:px-6 pb-5 pt-1 text-xs sm:text-sm text-purple-200/80 leading-relaxed border-t border-purple-500/15">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};
