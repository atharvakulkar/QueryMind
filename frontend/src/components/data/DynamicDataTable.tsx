import { type FC, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Download,
  Table2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface DynamicDataTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
  pageSize?: number;
}

export const DynamicDataTable: FC<DynamicDataTableProps> = ({
  columns,
  rows,
  pageSize = 10,
}) => {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, rows.length);
  const pageRows = rows.slice(startIdx, endIdx);

  /** Download data as CSV. */
  const downloadCSV = () => {
    const header = columns.join(',');
    const csvRows = rows.map((row) =>
      columns
        .map((col) => {
          const val = row[col];
          const str = val == null ? '' : String(val);
          return str.includes(',') || str.includes('"') || str.includes('\n')
            ? `"${str.replace(/"/g, '""')}"`
            : str;
        })
        .join(','),
    );
    const csv = [header, ...csvRows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'querymind_results.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatValue = (val: unknown): string => {
    if (val == null) return '—';
    if (typeof val === 'number') {
      return Number.isInteger(val) ? val.toLocaleString() : val.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
    if (typeof val === 'boolean') return val ? 'true' : 'false';
    return String(val);
  };

  return (
    <div className="rounded-xl border border-[var(--color-border-subtle)] overflow-hidden">
      {/* Table Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[var(--color-bg-tertiary)] border-b border-[var(--color-border-subtle)]">
        <div className="flex items-center gap-2">
          <Table2 className="w-3.5 h-3.5 text-[var(--color-brand-400)]" />
          <span className="text-xs font-medium text-[var(--color-text-secondary)]">
            {rows.length} row{rows.length !== 1 ? 's' : ''} · {columns.length} column{columns.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          onClick={downloadCSV}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-medium
            text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]
            transition-colors duration-150"
        >
          <Download className="w-3 h-3" />
          CSV
        </button>
      </div>

      {/* Scrollable Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border-subtle)] bg-[var(--color-bg-secondary)]">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-tertiary)] whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, rowIdx) => (
              <tr
                key={startIdx + rowIdx}
                className={cn(
                  'border-b border-[var(--color-border-subtle)] transition-colors duration-100',
                  rowIdx % 2 === 0
                    ? 'bg-transparent'
                    : 'bg-[var(--color-bg-secondary)]/50',
                  'hover:bg-[var(--color-bg-hover)]',
                )}
              >
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-4 py-2.5 text-xs text-[var(--color-text-primary)] whitespace-nowrap font-mono"
                  >
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-[var(--color-bg-tertiary)] border-t border-[var(--color-border-subtle)]">
          <span className="text-[10px] text-[var(--color-text-tertiary)]">
            Showing {startIdx + 1}–{endIdx} of {rows.length}
          </span>
          <div className="flex items-center gap-1">
            <PaginationButton
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
            >
              <ChevronsLeft className="w-3 h-3" />
            </PaginationButton>
            <PaginationButton
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-3 h-3" />
            </PaginationButton>
            <span className="px-3 text-[10px] font-medium text-[var(--color-text-secondary)]">
              {currentPage} / {totalPages}
            </span>
            <PaginationButton
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="w-3 h-3" />
            </PaginationButton>
            <PaginationButton
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
            >
              <ChevronsRight className="w-3 h-3" />
            </PaginationButton>
          </div>
        </div>
      )}
    </div>
  );
};

/* ===== Small pagination button ===== */
const PaginationButton: FC<{
  children: React.ReactNode;
  onClick: () => void;
  disabled: boolean;
}> = ({ children, onClick, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={cn(
      'p-1.5 rounded-md transition-colors duration-150',
      disabled
        ? 'text-[var(--color-text-tertiary)]/40 cursor-not-allowed'
        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]',
    )}
  >
    {children}
  </button>
);
