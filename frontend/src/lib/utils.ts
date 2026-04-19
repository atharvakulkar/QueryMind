import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge Tailwind classes with conflict resolution. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Generate a short unique ID. */
export function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}

/** Format a timestamp for display. */
export function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

/** Format milliseconds to a readable string. */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/** Truncate text to a max length. */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '…';
}

/** Detect a plausible chart type from column names and data. */
export function detectChartType(
  columns: string[],
  rows: Record<string, unknown>[],
): 'bar' | 'line' | 'area' | 'none' {
  if (rows.length < 2 || columns.length < 2) return 'none';

  const datePatterns = /date|time|year|month|day|quarter|week|period|created|updated/i;
  const hasDateCol = columns.some((c) => datePatterns.test(c));
  const hasNumericCol = columns.some((c) => {
    const val = rows[0]?.[c];
    return typeof val === 'number' || (typeof val === 'string' && !isNaN(Number(val)));
  });

  if (!hasNumericCol) return 'none';
  if (hasDateCol && rows.length > 3) return 'line';
  if (rows.length <= 15) return 'bar';
  return 'area';
}

/** Simple SQL keyword highlighter — returns JSX-safe segments. */
export function highlightSQL(sql: string): string {
  const keywords = [
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'JOIN', 'LEFT', 'RIGHT',
    'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT',
    'OFFSET', 'AS', 'IN', 'NOT', 'NULL', 'IS', 'BETWEEN', 'LIKE',
    'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'WITH', 'DISTINCT',
    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'CAST', 'UNION',
    'INTERSECT', 'EXCEPT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER',
    'DROP', 'TABLE', 'INDEX', 'VIEW', 'SCHEMA', 'ASC', 'DESC', 'FETCH',
    'NEXT', 'ROWS', 'ONLY', 'OVER', 'PARTITION', 'RANK', 'ROW_NUMBER',
    'DENSE_RANK', 'LEAD', 'LAG',
  ];
  const pattern = new RegExp(`\\b(${keywords.join('|')})\\b`, 'gi');
  return sql.replace(pattern, (match) => match.toUpperCase());
}
