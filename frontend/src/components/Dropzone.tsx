import React, { useCallback, useState } from 'react';
import { UploadCloud, File, Image as ImageIcon, Video, X, CheckCircle2, FileArchive } from 'lucide-react';

interface DropzoneProps {
  label: string;
  sublabel?: string;
  accept: string;
  fileType: 'image' | 'video' | 'zip' | 'any';
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
  maxSizeBytes?: number;
}

export const Dropzone: React.FC<DropzoneProps> = ({
  label,
  sublabel,
  accept,
  fileType,
  selectedFile,
  onFileSelect,
  maxSizeBytes = 100 * 1024 * 1024,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFile = useCallback((file: File) => {
    if (file.size > maxSizeBytes) {
      alert(`File size exceeds maximum limit of ${(maxSizeBytes / (1024 * 1024)).toFixed(0)} MB.`);
      return;
    }

    onFileSelect(file);

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  }, [maxSizeBytes, onFileSelect]);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  };

  const getFileIcon = () => {
    if (fileType === 'image') return ImageIcon;
    if (fileType === 'video') return Video;
    if (fileType === 'zip') return FileArchive;
    return File;
  };

  const Icon = getFileIcon();

  return (
    <div className="w-full space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-purple-200">
          {label}
        </label>
        {selectedFile && (
          <span className="text-xs font-mono text-fuchsia-300 flex items-center space-x-1 bg-purple-950/60 px-2 py-0.5 rounded-full border border-purple-500/30">
            <CheckCircle2 className="w-3 h-3 text-fuchsia-400" />
            <span>Ready ({formatSize(selectedFile.size)})</span>
          </span>
        )}
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-2xl p-6 transition-all duration-300 cursor-pointer flex flex-col items-center justify-center text-center overflow-hidden ${
          isDragging
            ? 'border-fuchsia-400 bg-purple-950/40 shadow-[0_0_25px_rgba(217,70,239,0.3)] scale-[1.01]'
            : selectedFile
            ? 'border-purple-500/40 bg-[#0d061c]/80 hover:border-purple-400/60'
            : 'border-purple-500/20 bg-[#0d061c]/50 hover:border-purple-500/40 hover:bg-[#14092b]/60'
        }`}
        onClick={() => {
          const input = document.createElement('input');
          input.type = 'file';
          input.accept = accept;
          input.onchange = (e) => {
            const files = (e.target as HTMLInputElement).files;
            if (files && files[0]) {
              handleFile(files[0]);
            }
          };
          input.click();
        }}
      >
        {selectedFile ? (
          <div className="flex flex-col items-center space-y-3 w-full py-1">
            {previewUrl ? (
              <div className="relative group w-28 h-28 rounded-xl overflow-hidden border border-purple-400/40 shadow-[0_0_15px_rgba(168,85,247,0.3)]">
                <img
                  src={previewUrl}
                  alt="Carrier Preview"
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={handleClear}
                  className="absolute top-1 right-1 p-1 rounded-full bg-purple-950/80 text-white hover:bg-rose-600 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="relative p-3.5 rounded-2xl bg-purple-950/60 border border-purple-500/30 text-fuchsia-300 shadow-sm">
                <Icon className="w-8 h-8" />
                <button
                  type="button"
                  onClick={handleClear}
                  className="absolute -top-1.5 -right-1.5 p-1 rounded-full bg-purple-900 border border-purple-500/40 text-purple-200 hover:bg-rose-600 hover:text-white transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}

            <div className="text-center max-w-sm">
              <p className="text-xs font-semibold text-white truncate max-w-xs">{selectedFile.name}</p>
              <p className="text-[11px] font-mono text-purple-300/60 mt-0.5">
                {selectedFile.type || 'Binary Archive'} • {formatSize(selectedFile.size)}
              </p>
            </div>

            <p className="text-[11px] text-fuchsia-400/80 underline font-medium">Click or drop to replace</p>
          </div>
        ) : (
          <div className="space-y-3 py-3">
            <div className="w-12 h-12 mx-auto rounded-full bg-purple-950/60 border border-purple-500/30 flex items-center justify-center text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
              <UploadCloud className="w-6 h-6 text-fuchsia-400" />
            </div>

            <div className="space-y-1">
              <p className="text-xs font-semibold text-white">
                Drop your carrier file here, or <span className="text-fuchsia-400 underline">browse</span>
              </p>
              <p className="text-[11px] text-purple-300/50">
                {sublabel || `Supported: ${accept}`}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
