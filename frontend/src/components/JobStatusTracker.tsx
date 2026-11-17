import React, { useEffect, useState } from 'react';
import { Clock, RefreshCw, CheckCircle2, AlertOctagon, Download, ShieldCheck, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import { JobRecord } from '../types';

interface JobStatusTrackerProps {
  jobId: string;
  initialJob?: JobRecord | null;
  onCompleted?: (job: JobRecord) => void;
}

export const JobStatusTracker: React.FC<JobStatusTrackerProps> = ({
  jobId,
  initialJob,
  onCompleted,
}) => {
  const [job, setJob] = useState<JobRecord | null>(initialJob || null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: any = null;

    const poll = async () => {
      try {
        const updated = await api.getJob(jobId);
        setJob(updated);
        if (updated.status === 'COMPLETED') {
          if (onCompleted) onCompleted(updated);
          clearInterval(interval);
        } else if (updated.status === 'FAILED') {
          clearInterval(interval);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to poll job status');
      }
    };

    poll();
    interval = setInterval(poll, 1500);

    return () => clearInterval(interval);
  }, [jobId, onCompleted]);

  if (error) {
    return (
      <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs font-mono">
        {error}
      </div>
    );
  }

  if (!job) return null;

  const steps = [
    { key: 'QUEUED', label: 'Queued' },
    { key: 'PROCESSING', label: 'Encrypt & Embed' },
    { key: 'VERIFYING', label: 'Forensic Check' },
    { key: 'COMPLETED', label: 'Ready' },
  ];

  const getStepIndex = (status: string) => {
    if (status === 'QUEUED') return 0;
    if (status === 'PROCESSING') return 1;
    if (status === 'VERIFYING') return 2;
    if (status === 'COMPLETED') return 3;
    return -1;
  };

  const currentIndex = getStepIndex(job.status);

  return (
    <div className="p-6 rounded-3xl glass-panel shadow-2xl space-y-6 relative overflow-hidden">
      {/* Top Laser Accent */}
      <div className="absolute top-0 left-0 right-0 laser-beam-sm" />

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {job.status === 'COMPLETED' ? (
            <div className="w-10 h-10 rounded-full bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(217,70,239,0.4)]">
              <CheckCircle2 className="w-5 h-5 text-fuchsia-400" />
            </div>
          ) : job.status === 'FAILED' ? (
            <div className="w-10 h-10 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 flex items-center justify-center">
              <AlertOctagon className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-10 h-10 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center justify-center animate-spin">
              <RefreshCw className="w-5 h-5 text-fuchsia-400" />
            </div>
          )}
          <div>
            <h4 className="text-sm font-heading font-bold text-white">
              {job.status === 'COMPLETED'
                ? 'Carrier Generation Complete'
                : job.status === 'FAILED'
                ? 'Carrier Processing Failed'
                : 'Asynchronous Embedding in Progress'}
            </h4>
            <p className="text-[11px] text-purple-300/60 font-mono mt-0.5">Job: {job.id}</p>
          </div>
        </div>

        <span className="text-xs font-mono font-semibold px-3 py-1 rounded-full bg-purple-950/70 border border-purple-500/30 text-purple-200">
          {job.status} ({job.progress}%)
        </span>
      </div>

      {/* Steps Pipeline */}
      {job.status !== 'FAILED' && (
        <div className="relative pt-2">
          <div className="grid grid-cols-4 gap-2 text-center">
            {steps.map((st, idx) => {
              const isPastOrCurrent = currentIndex >= idx;
              const isCurrent = currentIndex === idx;
              return (
                <div key={st.key} className="space-y-2">
                  <div className="flex items-center justify-center">
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all ${
                        isCurrent
                          ? 'bg-fuchsia-600 text-white shadow-[0_0_15px_rgba(217,70,239,0.7)] ring-2 ring-purple-400'
                          : isPastOrCurrent
                          ? 'bg-purple-900 text-purple-200 border border-purple-400/40'
                          : 'bg-[#0d061c] text-purple-500/40 border border-purple-500/20'
                      }`}
                    >
                      {idx + 1}
                    </div>
                  </div>
                  <span
                    className={`block text-[11px] font-medium ${
                      isPastOrCurrent ? 'text-white' : 'text-purple-400/40'
                    }`}
                  >
                    {st.label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="w-full bg-purple-950/60 h-1.5 rounded-full overflow-hidden mt-3 border border-purple-500/20">
            <div
              className="h-full bg-gradient-to-r from-purple-500 via-fuchsia-500 to-purple-400 transition-all duration-300 shadow-[0_0_10px_rgba(217,70,239,0.6)]"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Failure Info */}
      {job.status === 'FAILED' && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/40 text-xs text-rose-300 space-y-1">
          <p className="font-semibold text-rose-200">Error: {job.error_code || 'PROCESSING_ERROR'}</p>
          <p>{job.error_message || 'An error occurred during carrier encoding.'}</p>
        </div>
      )}

      {/* Download Action on Completion */}
      {job.status === 'COMPLETED' && job.download_url && (
        <div className="pt-2">
          <a
            href={job.download_url}
            download={job.filename || 'valicrypt_carrier'}
            className="w-full flex items-center justify-center space-x-2 py-3.5 px-6 rounded-xl text-xs sm:text-sm font-semibold tracking-wide text-white bg-gradient-to-r from-purple-600 via-fuchsia-600 to-purple-600 hover:from-purple-500 hover:to-fuchsia-500 shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all hover:scale-[1.01] border border-fuchsia-400/40"
          >
            <Download className="w-4 h-4" />
            <span>Download Encrypted Carrier ({job.filename || 'valicrypt_carrier'})</span>
          </a>
        </div>
      )}
    </div>
  );
};
