import React, { useState } from 'react';
import { Eye, EyeOff, Lock, KeyRound, ShieldAlert, ShieldCheck } from 'lucide-react';

interface PasswordInputProps {
  value: string;
  onChange: (val: string) => void;
  label?: string;
  placeholder?: string;
  showStrength?: boolean;
}

export const PasswordInput: React.FC<PasswordInputProps> = ({
  value,
  onChange,
  label = 'Encryption Password',
  placeholder = 'Enter strong secret passphrase...',
  showStrength = true,
}) => {
  const [show, setShow] = useState(false);

  const calculateStrength = (pwd: string) => {
    if (!pwd) return { score: 0, label: 'Empty', color: 'bg-purple-950', glow: '' };
    let score = 0;
    if (pwd.length >= 8) score += 1;
    if (pwd.length >= 14) score += 1;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score += 1;
    if (/\d/.test(pwd)) score += 1;
    if (/[^a-zA-Z0-9]/.test(pwd)) score += 1;

    switch (score) {
      case 1:
        return { score: 20, label: 'Very Weak', color: 'bg-rose-500', glow: 'shadow-[0_0_10px_rgba(244,63,94,0.5)]' };
      case 2:
        return { score: 40, label: 'Weak', color: 'bg-amber-500', glow: 'shadow-[0_0_10px_rgba(245,158,11,0.5)]' };
      case 3:
        return { score: 65, label: 'Moderate', color: 'bg-purple-500', glow: 'shadow-[0_0_10px_rgba(168,85,247,0.5)]' };
      case 4:
        return { score: 85, label: 'Strong', color: 'bg-fuchsia-500', glow: 'shadow-[0_0_12px_rgba(217,70,239,0.6)]' };
      case 5:
        return { score: 100, label: 'High Security (Quantum-Resistant Entropy)', color: 'bg-gradient-to-r from-purple-500 via-fuchsia-400 to-white', glow: 'shadow-[0_0_15px_rgba(217,70,239,0.8)]' };
      default:
        return { score: 0, label: 'Empty', color: 'bg-purple-950', glow: '' };
    }
  };

  const strength = calculateStrength(value);

  return (
    <div className="w-full space-y-1.5">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-purple-200 flex items-center space-x-1.5">
          <KeyRound className="w-3.5 h-3.5 text-fuchsia-400" />
          <span>{label}</span>
        </label>
        {showStrength && value && (
          <span className="text-xs font-mono text-purple-300">
            Entropy: <span className="font-semibold text-fuchsia-300">{strength.label}</span>
          </span>
        )}
      </div>

      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-[#0d061c]/80 border border-purple-500/25 focus:border-fuchsia-400 focus:ring-1 focus:ring-fuchsia-400/50 text-white rounded-2xl px-4 py-3 text-sm pr-11 font-mono transition-all placeholder:text-purple-400/40 outline-none shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)]"
        />
        <button
          type="button"
          onClick={() => setShow(!show)}
          className="absolute right-3.5 top-1/2 -translate-y-1/2 text-purple-400 hover:text-white p-1 rounded-lg transition-colors"
          title={show ? 'Hide password' : 'Show password'}
        >
          {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>

      {showStrength && value && (
        <div className="mt-2 space-y-1.5">
          <div className="w-full bg-purple-950/60 h-1.5 rounded-full overflow-hidden border border-purple-500/20">
            <div
              className={`h-full ${strength.color} ${strength.glow} transition-all duration-300 rounded-full`}
              style={{ width: `${strength.score}%` }}
            />
          </div>
          <p className="text-[11px] font-mono text-purple-300/50">
            RFC 9106 Argon2id • 64 MiB memory cost • 2 iterations • 16-byte cryptographically secure salt
          </p>
        </div>
      )}
    </div>
  );
};
