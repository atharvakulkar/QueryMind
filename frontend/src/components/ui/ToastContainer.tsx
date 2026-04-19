import { type FC } from 'react';
import { X, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import { useChatStore, type ToastItem } from '@/store/chatStore';
import { cn } from '@/lib/utils';

export const ToastContainer: FC = () => {
  const toasts = useChatStore((s) => s.toasts);
  const removeToast = useChatStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-viewport" role="region" aria-label="Notifications">
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onDismiss={removeToast} />
      ))}
    </div>
  );
};

const ToastCard: FC<{ toast: ToastItem; onDismiss: (id: string) => void }> = ({
  toast,
  onDismiss,
}) => {
  const Icon =
    toast.variant === 'destructive'
      ? AlertTriangle
      : toast.variant === 'success'
        ? CheckCircle2
        : Info;

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-xl shadow-lg animate-slide-up glass-panel-elevated',
        toast.variant === 'destructive' && 'border-[var(--color-error)]/30',
        toast.variant === 'success' && 'border-[var(--color-success)]/30',
      )}
    >
      <Icon
        className={cn(
          'w-4 h-4 mt-0.5 shrink-0',
          toast.variant === 'destructive' && 'text-[var(--color-error)]',
          toast.variant === 'success' && 'text-[var(--color-success)]',
          toast.variant === 'default' && 'text-[var(--color-info)]',
        )}
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[var(--color-text-primary)]">
          {toast.title}
        </p>
        {toast.description && (
          <p className="text-xs text-[var(--color-text-secondary)] mt-0.5 line-clamp-2">
            {toast.description}
          </p>
        )}
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="p-1 rounded-md hover:bg-[var(--color-bg-hover)] text-[var(--color-text-tertiary)] transition-colors duration-150"
        aria-label="Dismiss"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
