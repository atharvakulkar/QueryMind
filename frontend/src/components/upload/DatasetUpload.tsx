import { type FC, useState, useRef, useCallback } from 'react';
import { UploadCloud, FileType, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react';
import { uploadCSV, UploadError } from '@/services/uploadApi';
import type { UploadResponse } from '@/types';
import { useChatStore } from '@/store/chatStore';

export const DatasetUpload: FC = () => {
  const [isHovering, setIsHovering] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<UploadResponse | null>(null);
  
  const sendMessage = useChatStore((s) => s.sendMessage);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file) return;
    setError(null);
    setSuccess(null);

    if (file.type !== 'text/csv' && !file.name.toLowerCase().endsWith('.csv')) {
      setError('Only CSV files are supported.');
      return;
    }

    // Client-side size check (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be under 10MB.');
      return;
    }

    setIsUploading(true);
    try {
      const response = await uploadCSV(file);
      setSuccess(response);
    } catch (err) {
      setError(err instanceof UploadError ? err.message : 'An unexpected error occurred.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsHovering(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsHovering(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsHovering(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleQueryClick = useCallback(() => {
    if (success) {
      sendMessage(`Show me the first 10 rows of the ${success.table_name} dataset.`);
    }
  }, [success, sendMessage]);

  const reset = () => {
    setSuccess(null);
    setError(null);
  };

  return (
    <div className="w-full max-w-sm mx-auto">
      {success ? (
        <div className="rounded-xl border border-[var(--color-brand-500)]/30 bg-gradient-to-b from-[var(--color-brand-500)]/5 to-transparent p-5">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--color-brand-500)]/20 text-[var(--color-brand-400)]">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-[var(--color-text-primary)]">
                  Dataset Uploaded
                </h4>
                <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">
                  {success.row_count.toLocaleString()} rows • {success.columns.length} columns
                </p>
              </div>
            </div>
            <button
              onClick={reset}
              className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] transition-colors p-1"
              aria-label="Upload another"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-4 p-3 rounded-lg bg-[var(--color-bg-tertiary)] border border-[var(--color-border-subtle)]">
            <p className="text-xs text-[var(--color-text-secondary)] font-mono text-center">
              {success.fully_qualified}
            </p>
          </div>

          <button
            onClick={handleQueryClick}
            className="mt-4 w-full py-2.5 rounded-lg text-sm font-medium bg-[var(--color-bg-tertiary)] 
              border border-[var(--color-border-subtle)] text-[var(--color-text-primary)] 
              hover:border-[var(--color-brand-500)]/50 hover:bg-[var(--color-brand-500)]/5 
              hover:text-[var(--color-brand-400)] transition-all duration-200 shadow-sm"
          >
            Start Querying Data
          </button>
        </div>
      ) : (
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`
            relative overflow-hidden rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer
            ${isHovering 
              ? 'border-[var(--color-brand-400)] bg-[var(--color-brand-500)]/5 shadow-[var(--shadow-glow)] scale-[1.02]' 
              : 'border-[var(--color-border-subtle)] bg-[var(--color-bg-secondary)] hover:border-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-tertiary)]'
            }
            ${isUploading ? 'opacity-70 pointer-events-none' : ''}
          `}
        >
          <input
            type="file"
            accept=".csv"
            ref={fileInputRef}
            onChange={(e) => {
              if (e.target.files?.[0]) handleFile(e.target.files[0]);
            }}
            className="hidden"
          />

          <div className="p-6 text-center flex flex-col items-center justify-center min-h-[160px]">
            {isUploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 text-[var(--color-brand-400)] animate-spin" />
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">
                  Analyzing & Uploading...
                </p>
              </div>
            ) : (
              <>
                <div className="w-12 h-12 rounded-full bg-[var(--color-bg-tertiary)] flex items-center justify-center mb-3 shadow-inner">
                  {isHovering ? (
                    <UploadCloud className="w-6 h-6 text-[var(--color-brand-400)] animate-pulse" />
                  ) : (
                    <FileType className="w-6 h-6 text-[var(--color-text-tertiary)]" />
                  )}
                </div>
                <h4 className="text-sm font-medium text-[var(--color-text-primary)] mb-1">
                  Upload Custom Dataset
                </h4>
                <p className="text-xs text-[var(--color-text-tertiary)]">
                  Drag & drop a CSV file here, or click to browse
                </p>
              </>
            )}
          </div>

          {/* Error overlay */}
          {error && !isUploading && (
            <div className="absolute inset-0 bg-[var(--color-bg-secondary)]/95 backdrop-blur-sm flex flex-col items-center justify-center p-4 border border-[var(--color-warning)]/30 rounded-xl">
              <AlertCircle className="w-8 h-8 text-[var(--color-warning)] mb-2" />
              <p className="text-sm font-medium text-[var(--color-text-primary)] text-center mb-3">
                Upload Failed
              </p>
              <p className="text-xs text-[var(--color-warning)] text-center mb-4 leading-relaxed max-w-[250px]">
                {error}
              </p>
              <button
                onClick={(e) => { e.stopPropagation(); setError(null); }}
                className="px-4 py-1.5 rounded-lg text-xs font-medium bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-hover)] text-[var(--color-text-primary)] border border-[var(--color-border-subtle)] transition-colors"
                aria-label="Dismiss error"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
