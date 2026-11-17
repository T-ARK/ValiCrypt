import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

interface AlertBannerProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  onClose?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type,
  title,
  message,
  onClose,
}) => {
  const styles = {
    success: {
      bg: 'bg-[#120826]/80 border-fuchsia-500/40 text-purple-100 shadow-[0_0_20px_rgba(217,70,239,0.15)]',
      icon: CheckCircle2,
      iconColor: 'text-fuchsia-400',
    },
    error: {
      bg: 'bg-rose-950/40 border-rose-500/40 text-rose-200 shadow-[0_0_20px_rgba(244,63,94,0.15)]',
      icon: AlertCircle,
      iconColor: 'text-rose-400',
    },
    warning: {
      bg: 'bg-amber-950/40 border-amber-500/40 text-amber-200 shadow-[0_0_20px_rgba(245,158,11,0.15)]',
      icon: AlertTriangle,
      iconColor: 'text-amber-400',
    },
    info: {
      bg: 'bg-[#120826]/80 border-purple-500/30 text-purple-200 shadow-[0_0_20px_rgba(168,85,247,0.15)]',
      icon: Info,
      iconColor: 'text-purple-400',
    },
  }[type];

  const Icon = styles.icon;

  return (
    <div className={`p-4 rounded-2xl border backdrop-blur-md flex items-start space-x-3 text-xs sm:text-sm ${styles.bg}`}>
      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${styles.iconColor}`} />
      <div className="flex-1">
        {title && <h4 className="font-heading font-bold mb-0.5 text-white">{title}</h4>}
        <p className="leading-relaxed opacity-90">{message}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-1 rounded-lg opacity-60 hover:opacity-100 hover:bg-white/10 transition-opacity"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
