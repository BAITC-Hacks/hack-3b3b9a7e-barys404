import { useEffect, useRef, useState } from 'react'
import { day, decimal, number, shortDay } from '../../lib/format'
import { EmptyState } from '../ui/EmptyState'

export function TrendChart({
  rows,
  forecastFrom,
}: {
  rows: {
    date: string
    value: number
  }[]
  forecastFrom?: number
}) {
  const [active, setActive] = useState<number | null>(null)
  const chartRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(760)
  const hasRows = rows.length > 0
  useEffect(() => {
    if (!chartRef.current) return
    // Match the drawing to its container so labels stay readable on narrow cards.
    const observer = new ResizeObserver(([entry]) =>
      setWidth(Math.max(1, Math.round(entry.contentRect.width))),
    )
    observer.observe(chartRef.current)
    return () => observer.disconnect()
  }, [hasRows])
  if (!rows.length)
    return (
      <EmptyState title="Нет данных для графика" text="Попробуйте изменить период или фильтры." />
    )
  const height = 280,
    left = 68,
    right = 16,
    top = 24,
    bottom = 51
  const plotWidth = width - left - right,
    plotHeight = height - top - bottom
  const max = Math.max(1, ...rows.map((row) => row.value))
  const topValue = Math.ceil(max / 5) * 5 || 5
  const x = (index: number) =>
    left + (rows.length === 1 ? plotWidth / 2 : (index / (rows.length - 1)) * plotWidth)
  const y = (value: number) => top + plotHeight - (value / topValue) * plotHeight
  const points = rows.map((row, index) => `${x(index)},${y(row.value)}`)
  const observed = forecastFrom == null ? points : points.slice(0, forecastFrom)
  const projected = forecastFrom == null ? [] : points.slice(Math.max(0, forecastFrom - 1))
  const area = `M ${x(0)} ${top + plotHeight} L ${points.join(' L ')} L ${x(rows.length - 1)} ${top + plotHeight} Z`
  const labels = [...new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1])]
  const current = active == null ? null : rows[active]
  const tipX = active == null ? 0 : Math.min(width - 186, Math.max(6, x(active) - 90))
  return (
    <div className="chart-wrap" ref={chartRef}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="График направлений по датам"
        onMouseLeave={() => setActive(null)}
      >
        <defs>
          <linearGradient id="chartArea" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#24a99a" stopOpacity=".2" />
            <stop offset="100%" stopColor="#24a99a" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 0.5, 1].map((fraction, index) => (
          <g key={index}>
            <line
              x1={left}
              x2={width - right}
              y1={y(topValue * fraction)}
              y2={y(topValue * fraction)}
              className="chart-grid"
            />
            <text
              x={left - 10}
              y={y(topValue * fraction) + 4}
              textAnchor="end"
              className="chart-label"
            >
              {number(topValue * fraction)}
            </text>
          </g>
        ))}
        {forecastFrom != null && (
          <rect
            x={x(Math.max(0, forecastFrom - 1))}
            y={top}
            width={width - right - x(Math.max(0, forecastFrom - 1))}
            height={plotHeight}
            fill="#e8f3f1"
            opacity=".8"
          />
        )}
        <path d={area} fill="url(#chartArea)" opacity={forecastFrom == null ? 1 : 0.5} />
        <polyline
          points={observed.join(' ')}
          fill="none"
          stroke="#147c78"
          strokeWidth="3.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {rows.length === 1 && <circle cx={x(0)} cy={y(rows[0].value)} r="5" fill="#147c78" />}
        {projected.length > 1 && (
          <polyline
            points={projected.join(' ')}
            fill="none"
            stroke="#39a9a0"
            strokeWidth="3.3"
            strokeDasharray="7 6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
        {labels.map((index) => (
          <text
            key={index}
            x={x(index)}
            y={height - 14}
            textAnchor={index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle'}
            className="chart-label"
          >
            {shortDay(rows[index].date)}
          </text>
        ))}
        {rows.map((row, index) => (
          <circle
            key={`${row.date}-${index}`}
            cx={x(index)}
            cy={y(row.value)}
            r="12"
            fill="transparent"
            onMouseEnter={() => setActive(index)}
            onFocus={() => setActive(index)}
            tabIndex={0}
            aria-label={`${day(row.date)}: ${decimal(row.value)} направлений`}
          />
        ))}
        {active != null && current && (
          <g className="chart-tip">
            <line
              x1={x(active)}
              x2={x(active)}
              y1={top}
              y2={top + plotHeight}
              stroke="#71bcb4"
              strokeDasharray="4 5"
            />
            <circle
              cx={x(active)}
              cy={y(current.value)}
              r="5"
              fill="#147c78"
              stroke="white"
              strokeWidth="2"
            />
            <rect x={tipX} y="2" width="180" height="61" rx="10" fill="#143d43" />
            <text x={tipX + 11} y="25" fill="#bed8d7" fontSize="14">
              {day(current.date)}
            </text>
            <text x={tipX + 11} y="49" fill="white" fontSize="16" fontWeight="700">
              {decimal(current.value)} направл.
            </text>
          </g>
        )}
      </svg>
    </div>
  )
}
