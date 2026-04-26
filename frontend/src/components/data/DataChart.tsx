import { type FC, useCallback, useMemo, useRef } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { BarChart3, Download } from 'lucide-react';
import type { ChartType } from '@/types';

interface DataChartProps {
  columns: string[];
  rows: Record<string, unknown>[];
  chartType: ChartType;
}

/** HSL colors for chart series. */
const CHART_COLORS = [
  '#818cf8', // brand-400
  '#a855f7', // accent-500
  '#34d399', // success
  '#fbbf24', // warning
  '#60a5fa', // info
  '#f87171', // error
  '#c084fc', // accent-400
  '#fb923c', // orange
];

export const DataChart: FC<DataChartProps> = ({ columns, rows, chartType }) => {
  /** Determine the category (x-axis) and numeric (y-axis) columns. */
  const { categoryCol, numericCols, chartData } = useMemo(() => {
    /* First column is typically the category/label. */
    const catCol = columns[0];
    const numCols = columns.slice(1).filter((col) => {
      const sample = rows[0]?.[col];
      return (
        typeof sample === 'number' ||
        (typeof sample === 'string' && !isNaN(Number(sample)))
      );
    });

    const data = rows.map((row) => {
      const entry: Record<string, unknown> = { [catCol]: String(row[catCol] ?? '') };
      numCols.forEach((col) => {
        const raw = row[col];
        entry[col] = typeof raw === 'number' ? raw : Number(raw);
      });
      return entry;
    });

    return { categoryCol: catCol, numericCols: numCols, chartData: data };
  }, [columns, rows]);

  if (numericCols.length === 0) return null;

  const chartRef = useRef<HTMLDivElement>(null);

  /** Export chart area to PNG via SVG serialisation + canvas rasterisation. */
  const exportPNG = useCallback(() => {
    const container = chartRef.current;
    if (!container) return;
    const svg = container.querySelector('svg');
    if (!svg) return;

    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svg);
    const svgBlob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const scale = 2; // retina-quality
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.fillStyle = '#0f1117'; // match dark bg
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(scale, scale);
      ctx.drawImage(img, 0, 0);
      const pngUrl = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = pngUrl;
      a.download = `querymind_chart_${chartType}.png`;
      a.click();
      URL.revokeObjectURL(url);
    };
    img.src = url;
  }, [chartType]);

  const commonProps = {
    data: chartData,
    margin: { top: 8, right: 16, left: 0, bottom: 0 },
  };

  const renderChart = () => {
    switch (chartType) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey={categoryCol}
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 11, color: '#94a3b8' }}
            />
            {numericCols.map((col, i) => (
              <Line
                key={col}
                type="monotone"
                dataKey={col}
                stroke={CHART_COLORS[i % CHART_COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3, fill: CHART_COLORS[i % CHART_COLORS.length] }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            <defs>
              {numericCols.map((col, i) => (
                <linearGradient key={col} id={`area-${i}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey={categoryCol}
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
            {numericCols.map((col, i) => (
              <Area
                key={col}
                type="monotone"
                dataKey={col}
                stroke={CHART_COLORS[i % CHART_COLORS.length]}
                strokeWidth={2}
                fill={`url(#area-${i})`}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
      default:
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey={categoryCol}
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
            {numericCols.map((col, i) => (
              <Bar
                key={col}
                dataKey={col}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
                radius={[4, 4, 0, 0]}
                maxBarSize={48}
              />
            ))}
          </BarChart>
        );
    }
  };

  return (
    <div className="rounded-xl border border-[var(--color-border-subtle)] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 bg-[var(--color-bg-tertiary)] border-b border-[var(--color-border-subtle)]">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-3.5 h-3.5 text-[var(--color-brand-400)]" />
          <span className="text-xs font-medium text-[var(--color-text-secondary)] capitalize">
            {chartType} Chart
          </span>
        </div>
        <button
          onClick={exportPNG}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-medium
            text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]
            transition-colors duration-150"
        >
          <Download className="w-3 h-3" />
          PNG
        </button>
      </div>
      <div ref={chartRef} className="p-4 bg-[var(--color-bg-secondary)]">
        <ResponsiveContainer width="100%" height={320}>
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/* ===== Custom Tooltip ===== */
interface TooltipPayload {
  name: string;
  value: number;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

const CustomTooltip: FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="glass-panel-elevated rounded-lg px-3 py-2 shadow-lg">
      <p className="text-[10px] font-semibold text-[var(--color-text-primary)] mb-1">
        {label}
      </p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 text-[11px]">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-[var(--color-text-secondary)]">{entry.name}:</span>
          <span className="font-medium text-[var(--color-text-primary)]">
            {typeof entry.value === 'number'
              ? entry.value.toLocaleString()
              : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};
