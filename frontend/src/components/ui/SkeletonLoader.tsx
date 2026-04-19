import type { FC } from 'react';

/** Skeleton loader displayed while the agent is processing. */
export const SkeletonLoader: FC = () => {
  return (
    <div className="space-y-4">
      {/* Thought process skeleton */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded animate-shimmer" />
          <div className="h-3.5 w-28 rounded-md animate-shimmer" />
        </div>
      </div>

      {/* Text skeleton */}
      <div className="space-y-2">
        <div className="h-3.5 w-full rounded-md animate-shimmer" />
        <div className="h-3.5 w-3/4 rounded-md animate-shimmer" />
        <div className="h-3.5 w-5/6 rounded-md animate-shimmer" />
      </div>

      {/* Table skeleton */}
      <div className="rounded-xl border border-[var(--color-border-subtle)] overflow-hidden">
        <div className="flex gap-4 px-4 py-3 bg-[var(--color-bg-tertiary)]">
          <div className="h-3 w-20 rounded-md animate-shimmer" />
          <div className="h-3 w-24 rounded-md animate-shimmer" />
          <div className="h-3 w-16 rounded-md animate-shimmer" />
        </div>
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="flex gap-4 px-4 py-3 border-t border-[var(--color-border-subtle)]"
          >
            <div className="h-3 w-20 rounded-md animate-shimmer" />
            <div className="h-3 w-24 rounded-md animate-shimmer" />
            <div className="h-3 w-16 rounded-md animate-shimmer" />
          </div>
        ))}
      </div>

      {/* Animated dots */}
      <div className="dot-pulse-container">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
};
