import { useState, useEffect, useRef, createContext, useContext } from 'react'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'

// ─── Types ──────────────────────────────────────────────────────────────────

type AppFlow = 'landing' | 'auth' | 'app'
type AuthTab = 'login' | 'signup'

type Screen =
  | 'dashboard'
  | 'inference'
  | 'benchmark'
  | 'optimization'
  | 'recommendations'
  | 'reports'
  | 'history'
  | 'settings'

// ─── Theme ───────────────────────────────────────────────────────────────────

const darkTheme = {
  bg: '#0b0e14',
  cardBg: '#141820',
  innerSurface: '#0b0e14',
  sidebarBg: '#0e1218',
  surface: '#1a1f2e',
  progressTrack: '#1e2433',
  text: '#e2e8f0',
  textHeading: '#f1f5f9',
  textSecondary: '#64748b',
  textMuted: '#475569',
  textFaint: '#334155',
  textDim: '#94a3b8',
  border: 'rgba(255,255,255,0.07)',
  borderInput: 'rgba(255,255,255,0.1)',
  divider: 'rgba(255,255,255,0.06)',
  rowDivider: 'rgba(255,255,255,0.04)',
  ghostBg: 'rgba(255,255,255,0.05)',
  ghostBgHover: 'rgba(255,255,255,0.08)',
  ghostBorder: 'rgba(255,255,255,0.12)',
  ghostBorderHover: 'rgba(255,255,255,0.35)',
  navActive: 'rgba(249,115,22,0.12)',
  navHover: 'rgba(255,255,255,0.04)',
  scrolledHeaderBg: 'rgba(11,14,20,0.95)',
  tooltipBg: '#1a1f2e',
  inputBg: '#0b0e14',
  cyan: '#06b6d4',
  green: '#22c55e',
  purple: '#a78bfa',
  red: '#ef4444',
  orange: '#f97316',
  yellow: '#eab308',
  highlightedText: '#94a3b8',
  opaqueTextOnOrange: '#0b0e14',
}

const lightTheme = {
  bg: '#FAF6EF',
  cardBg: '#F0E8D8',
  innerSurface: '#E8DFD0',
  sidebarBg: '#EDE5D5',
  surface: '#EDE5D5',
  progressTrack: 'rgba(0,0,0,0.08)',
  text: '#1A1410',
  textHeading: '#0D0A07',
  textSecondary: '#6B6355',
  textMuted: '#8B7D6B',
  textFaint: '#A09080',
  textDim: '#5A5248',
  border: 'rgba(139,109,81,0.14)',
  borderInput: 'rgba(139,109,81,0.25)',
  divider: 'rgba(139,109,81,0.12)',
  rowDivider: 'rgba(139,109,81,0.08)',
  ghostBg: 'rgba(0,0,0,0.04)',
  ghostBgHover: 'rgba(0,0,0,0.07)',
  ghostBorder: 'rgba(0,0,0,0.18)',
  ghostBorderHover: 'rgba(0,0,0,0.35)',
  navActive: 'rgba(249,115,22,0.1)',
  navHover: 'rgba(0,0,0,0.04)',
  scrolledHeaderBg: 'rgba(250,246,239,0.95)',
  tooltipBg: '#EDE5D5',
  inputBg: '#F7F2EA',
  cyan: '#0891b2',
  green: '#16a34a',
  purple: '#7c3aed',
  red: '#dc2626',
  orange: '#f97316',
  yellow: '#ca8a04',
  highlightedText: '#5A5248',
  opaqueTextOnOrange: '#fff',
}

type Theme = typeof darkTheme

const ThemeContext = createContext<{ t: Theme; isDark: boolean; setIsDark: (v: boolean | ((p: boolean) => boolean)) => void }>({
  t: darkTheme, isDark: true, setIsDark: () => {},
})

function useTheme() { return useContext(ThemeContext) }

// ─── Mock Data ───────────────────────────────────────────────────────────────

const throughputData = [
  { t: '00:00', before: 12.4, after: 28.1 },
  { t: '00:05', before: 11.8, after: 29.3 },
  { t: '00:10', before: 13.1, after: 31.2 },
  { t: '00:15', before: 12.0, after: 30.8 },
  { t: '00:20', before: 14.2, after: 33.5 },
  { t: '00:25', before: 13.5, after: 32.1 },
  { t: '00:30', before: 12.9, after: 34.7 },
]

const latencyData = [
  { t: '00:00', p50: 82, p95: 140, p99: 210 },
  { t: '00:05', p50: 79, p95: 135, p99: 198 },
  { t: '00:10', p50: 75, p95: 128, p99: 187 },
  { t: '00:15', p50: 71, p95: 121, p99: 174 },
  { t: '00:20', p50: 68, p95: 115, p99: 162 },
  { t: '00:25', p50: 65, p95: 109, p99: 155 },
  { t: '00:30', p50: 62, p95: 104, p99: 147 },
]

const cpuData = [
  { t: '0s', cpu: 34 }, { t: '10s', cpu: 58 }, { t: '20s', cpu: 72 },
  { t: '30s', cpu: 81 }, { t: '40s', cpu: 76 }, { t: '50s', cpu: 88 },
  { t: '60s', cpu: 84 }, { t: '70s', cpu: 79 }, { t: '80s', cpu: 91 },
  { t: '90s', cpu: 86 },
]

const benchmarkRuns = [
  { id: 'RUN-0042', model: 'Llama-3.2-3B', config: 'INT4 + batch=8', ttft: '48ms', tps: '34.7', p95: '104ms', status: 'pass' },
  { id: 'RUN-0041', model: 'Llama-3.2-3B', config: 'FP16 baseline', ttft: '127ms', tps: '12.9', p95: '310ms', status: 'pass' },
  { id: 'RUN-0040', model: 'Mistral-7B', config: 'INT8 + batch=4', ttft: '91ms', tps: '18.2', p95: '198ms', status: 'pass' },
  { id: 'RUN-0039', model: 'Phi-3-mini', config: 'INT4 + threads=16', ttft: '31ms', tps: '51.3', p95: '78ms', status: 'pass' },
  { id: 'RUN-0038', model: 'Mistral-7B', config: 'FP32 baseline', ttft: '204ms', tps: '7.1', p95: '489ms', status: 'fail' },
]

const models = [
  { id: 'llama-3.2-3b', name: 'Llama 3.2 3B', params: '3.2B', quant: 'INT4', size: '2.1 GB', provider: 'Meta' },
  { id: 'mistral-7b', name: 'Mistral 7B Instruct', params: '7.2B', quant: 'INT8', size: '7.3 GB', provider: 'Mistral AI' },
  { id: 'phi-3-mini', name: 'Phi-3 Mini', params: '3.8B', quant: 'INT4', size: '2.4 GB', provider: 'Microsoft' },
  { id: 'gemma-2b', name: 'Gemma 2B', params: '2.0B', quant: 'INT8', size: '2.9 GB', provider: 'Google' },
  { id: 'qwen-7b', name: 'Qwen2.5 7B', params: '7.6B', quant: 'INT4', size: '4.8 GB', provider: 'Alibaba' },
]

const comparisonData = [
  { label: 'TTFT', before: 127, after: 48, unit: 'ms', lowerBetter: true },
  { label: 'Tokens/sec', before: 12.9, after: 34.7, unit: '', lowerBetter: false },
  { label: 'P95 Latency', before: 310, after: 104, unit: 'ms', lowerBetter: true },
  { label: 'P99 Latency', before: 481, after: 162, unit: 'ms', lowerBetter: true },
  { label: 'CPU Util %', before: 91, after: 84, unit: '%', lowerBetter: true },
  { label: 'Mem Usage', before: 6.8, after: 3.2, unit: 'GB', lowerBetter: true },
]

// ─── Components ──────────────────────────────────────────────────────────────

function MetricCard({ label, value, unit, sub, trend, color = '#f97316' }: {
  label: string; value: string; unit?: string; sub?: string; trend?: string; color?: string
}) {
  const { t } = useTheme()
  const isPositive = trend?.startsWith('+')
  return (
    <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }}
      className="p-4 flex flex-col gap-1.5 hover:border-orange-500/20 transition-colors duration-200">
      <div style={{ color: t.textMuted, fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', fontFamily: 'JetBrains Mono, monospace' }}>{label}</div>
      <div className="flex items-baseline gap-1.5">
        <span style={{ fontSize: 28, fontWeight: 700, color, lineHeight: 1, fontFamily: 'JetBrains Mono, monospace' }}>{value}</span>
        {unit && <span style={{ fontSize: 12, color: t.textSecondary }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: 12, color: t.textSecondary }}>{sub}</div>}
      {trend && (
        <div style={{ fontSize: 11, color: isPositive ? t.green : t.red, fontFamily: 'JetBrains Mono, monospace' }}>
          {trend}
        </div>
      )}
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  const { t } = useTheme()
  return (
    <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.12em', textTransform: 'uppercase', color: t.textSecondary }}>
      {children}
    </div>
  )
}

function ChartCard({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  const { t } = useTheme()
  return (
    <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <SectionLabel>{title}</SectionLabel>
        {action}
      </div>
      {children}
    </div>
  )
}

function Badge({ children, color = '#f97316' }: { children: React.ReactNode; color?: string }) {
  return (
    <span style={{ background: `${color}18`, color, border: `1px solid ${color}30`, borderRadius: 4, padding: '2px 8px', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}>
      {children}
    </span>
  )
}

function Btn({ children, variant = 'primary', onClick, disabled, small }: {
  children: React.ReactNode; variant?: 'primary' | 'ghost' | 'danger' | 'cyan'; onClick?: () => void; disabled?: boolean; small?: boolean
}) {
  const { t } = useTheme()
  const styles: Record<string, React.CSSProperties> = {
    primary: { background: t.orange, color: t.opaqueTextOnOrange, border: 'none' },
    ghost: { background: t.ghostBg, color: t.text, border: `1px solid ${t.ghostBorder}` },
    danger: { background: `${t.red}20`, color: t.red, border: `1px solid ${t.red}30` },
    cyan: { background: `${t.cyan}20`, color: t.cyan, border: `1px solid ${t.cyan}30` },
  }
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        ...styles[variant],
        borderRadius: 5,
        padding: small ? '5px 12px' : '8px 18px',
        fontSize: small ? 11 : 13,
        fontWeight: 600,
        fontFamily: 'Inter, sans-serif',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'opacity 0.15s',
      }}
    >
      {children}
    </button>
  )
}

function Slider({ label, value, min, max, step, onChange, unit }: {
  label: string; value: number; min: number; max: number; step: number; onChange: (v: number) => void; unit?: string
}) {
  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span style={{ fontSize: 13, color: t.textDim }}>{label}</span>
        <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: t.orange }}>{value}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{ width: '100%', accentColor: t.orange, cursor: 'pointer' }}
      />
      <div className="flex justify-between" style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace' }}>
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  )
}

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  const { t } = useTheme()
  return (
    <button onClick={() => onChange(!value)} style={{
      width: 40, height: 22, borderRadius: 11,
      background: value ? t.orange : t.progressTrack,
      border: `1px solid ${t.borderInput}`,
      cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
    }}>
      <span style={{
        position: 'absolute', top: 2, left: value ? 18 : 2,
        width: 16, height: 16, borderRadius: '50%',
        background: value ? t.opaqueTextOnOrange : t.textMuted,
        transition: 'left 0.2s',
      }} />
    </button>
  )
}

// ─── Screens ─────────────────────────────────────────────────────────────────

function Dashboard() {
  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div className="flex items-center justify-between">
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>System Overview</div>
          <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>Arm Neoverse N1 · 64-core · 128 GB · ArmPilot v2.4.1</div>
        </div>
        <div className="flex items-center gap-3">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: t.green }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: t.green, display: 'inline-block', animation: 'pulse-dot 2s ease infinite' }} />
            Inference Server Online
          </div>
          <Btn variant="primary" small>+ New Benchmark</Btn>
        </div>
      </div>

      {/* Metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <MetricCard label="TTFT" value="48" unit="ms" trend="−62% vs baseline" color="#06b6d4" />
        <MetricCard label="Tokens / sec" value="34.7" trend="+169% vs baseline" color="#22c55e" />
        <MetricCard label="P95 Latency" value="104" unit="ms" trend="−66% vs baseline" color="#f97316" />
        <MetricCard label="Throughput" value="2,840" unit="tok/min" trend="+2.7× vs baseline" color="#a78bfa" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <MetricCard label="CPU Utilization" value="84" unit="%" sub="64 cores active" color="#f97316" />
        <MetricCard label="Memory Usage" value="3.2" unit="GB" sub="Model: Llama-3.2-3B INT4" color="#06b6d4" />
        <MetricCard label="Model Size" value="2.1" unit="GB" sub="INT4 quantized" color="#a78bfa" />
        <MetricCard label="Active Sessions" value="12" sub="max concurrency: 16" color="#22c55e" />
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <ChartCard title="Throughput — Before vs After">
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={throughputData}>
              <defs>
                <linearGradient id="gbefore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gafter" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={t.divider} />
              <XAxis dataKey="t" tick={{ fill: t.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: t.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: t.tooltipBg, border: `1px solid ${t.border}`, borderRadius: 6, fontSize: 12 }} />
              <Area type="monotone" dataKey="before" stroke="#f97316" fill="url(#gbefore)" strokeWidth={2} name="Before" />
              <Area type="monotone" dataKey="after" stroke={t.green} fill="url(#gafter)" strokeWidth={2} name="After" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Latency Distribution (ms)">
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke={t.divider} />
              <XAxis dataKey="t" tick={{ fill: t.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: t.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: t.tooltipBg, border: `1px solid ${t.border}`, borderRadius: 6, fontSize: 12 }} />
              <Line type="monotone" dataKey="p50" stroke={t.cyan} strokeWidth={2} dot={false} name="P50" />
              <Line type="monotone" dataKey="p95" stroke="#f97316" strokeWidth={2} dot={false} name="P95" />
              <Line type="monotone" dataKey="p99" stroke={t.red} strokeWidth={2} dot={false} name="P99" />
              <Legend iconType="line" wrapperStyle={{ fontSize: 11, color: t.textSecondary }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Recent runs */}
      <ChartCard title="Recent Benchmark Runs" action={<Btn variant="ghost" small>View All →</Btn>}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${t.divider}` }}>
              {['Run ID', 'Model', 'Configuration', 'TTFT', 'Tokens/sec', 'P95', 'Status'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '0 12px 10px 0', fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {benchmarkRuns.map((r, i) => (
              <tr key={r.id} style={{ borderBottom: i < benchmarkRuns.length - 1 ? `1px solid ${t.rowDivider}` : 'none' }}>
                <td style={{ padding: '10px 12px 10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.cyan }}>{r.id}</td>
                <td style={{ padding: '10px 12px 10px 0', fontSize: 13, color: t.text }}>{r.model}</td>
                <td style={{ padding: '10px 12px 10px 0', fontSize: 12, color: t.textDim }}>{r.config}</td>
                <td style={{ padding: '10px 12px 10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.text }}>{r.ttft}</td>
                <td style={{ padding: '10px 12px 10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.green }}>{r.tps}</td>
                <td style={{ padding: '10px 12px 10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.text }}>{r.p95}</td>
                <td style={{ padding: '10px 12px 10px 0' }}>
                  <Badge color={r.status === 'pass' ? t.green : t.red}>{r.status.toUpperCase()}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </ChartCard>
    </div>
  )
}

function Inference() {
  const [selectedModel, setSelectedModel] = useState('llama-3.2-3b')
  const [prompt, setPrompt] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [output, setOutput] = useState('')
  const [maxTokens, setMaxTokens] = useState(512)
  const [temperature, setTemperature] = useState(0.7)
  const streamRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const model = models.find(m => m.id === selectedModel)!

  const SAMPLE_RESPONSE = `The Arm Neoverse N1 platform delivers exceptional performance for LLM inference workloads. With its high core count and memory bandwidth, it enables efficient execution of quantized models.

Key advantages include:
- SVE2 vector extensions for SIMD acceleration
- High memory bandwidth (204 GB/s)
- Power-efficient compute fabric
- NUMA-aware scheduling support

When paired with INT4 quantization and optimized thread affinity, throughput improvements of 2-3× over baseline FP16 are achievable on this platform.`

  function runInference() {
    if (!prompt.trim() || streaming) return
    setOutput('')
    setStreaming(true)
    let i = 0
    streamRef.current = setInterval(() => {
      i += Math.floor(Math.random() * 3) + 1
      setOutput(SAMPLE_RESPONSE.slice(0, i))
      if (i >= SAMPLE_RESPONSE.length) {
        clearInterval(streamRef.current!)
        setStreaming(false)
      }
    }, 30)
  }

  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div className="flex items-center justify-between">
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>Model Inference</div>
          <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>Interactive inference with real-time performance monitoring</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>
        <div className="flex flex-col gap-4">
          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4">
            <SectionLabel>Select Model</SectionLabel>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 12 }}>
              {models.map(m => (
                <button key={m.id} onClick={() => setSelectedModel(m.id)} style={{
                  background: selectedModel === m.id ? t.navActive : t.ghostBg,
                  border: selectedModel === m.id ? `1px solid ${t.orange}50` : `1px solid ${t.border}`,
                  borderRadius: 5, padding: '10px 14px', textAlign: 'left', cursor: 'pointer', transition: 'all 0.15s'
                }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: selectedModel === m.id ? t.orange : t.text }}>{m.name}</div>
                  <div style={{ fontSize: 11, color: t.textSecondary, marginTop: 3, fontFamily: 'JetBrains Mono, monospace' }}>{m.params} · {m.quant} · {m.size}</div>
                </button>
              ))}
            </div>
          </div>

          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-3">
            <SectionLabel>Prompt</SectionLabel>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Enter your prompt here..."
              style={{
                background: t.inputBg, border: `1px solid ${t.borderInput}`, borderRadius: 5,
                color: t.text, padding: '12px 14px', fontSize: 13, resize: 'vertical',
                minHeight: 100, fontFamily: 'Inter, sans-serif', outline: 'none',
              }}
            />
            <div className="flex justify-end">
              <Btn variant="primary" onClick={runInference} disabled={streaming || !prompt.trim()}>
                {streaming ? '⟳ Generating...' : '▶ Run Inference'}
              </Btn>
            </div>
          </div>

          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <SectionLabel>Output</SectionLabel>
              {streaming && <Badge color={t.green}>STREAMING</Badge>}
            </div>
            <div style={{
              background: t.innerSurface, border: `1px solid ${t.border}`, borderRadius: 5,
              padding: '14px', fontSize: 13, minHeight: 160, color: t.text, lineHeight: 1.7,
              fontFamily: 'Inter, sans-serif', whiteSpace: 'pre-wrap', transition: 'background 0.3s',
            }}>
              {output || <span style={{ color: t.textMuted }}>Output will appear here...</span>}
              {streaming && <span className="streaming-cursor" />}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-4">
            <SectionLabel>Generation Settings</SectionLabel>
            <Slider label="Max Tokens" value={maxTokens} min={64} max={2048} step={64} onChange={setMaxTokens} />
            <Slider label="Temperature" value={temperature} min={0} max={2} step={0.1} onChange={setTemperature} />
          </div>

          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-3">
            <SectionLabel>Model Information</SectionLabel>
            {[
              ['Model', model.name],
              ['Parameters', model.params],
              ['Quantization', model.quant],
              ['Model Size', model.size],
              ['Provider', model.provider],
              ['Runtime', 'llama.cpp'],
              ['Backend', 'Arm NEON + SVE2'],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between" style={{ fontSize: 12, borderBottom: `1px solid ${t.rowDivider}`, paddingBottom: 8 }}>
                <span style={{ color: t.textSecondary }}>{k}</span>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', color: t.text }}>{v}</span>
              </div>
            ))}
          </div>

          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-3">
            <SectionLabel>Live Metrics</SectionLabel>
            {[
              ['TTFT', '48 ms', t.cyan],
              ['Tokens/sec', '34.7', t.green],
              ['Memory', '3.2 GB', t.orange],
            ].map(([k, v, c]) => (
              <div key={k} className="flex justify-between items-center">
                <span style={{ fontSize: 12, color: t.textSecondary }}>{k}</span>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700, color: c }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Benchmark() {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [concurrency, setConcurrency] = useState(4)
  const [duration, setDuration] = useState(60)
  const [selectedModel, setSelectedModel] = useState('llama-3.2-3b')
  const [done, setDone] = useState(false)

  function runBenchmark() {
    setRunning(true)
    setProgress(0)
    setDone(false)
    const iv = setInterval(() => {
      setProgress(p => {
        if (p >= 100) { clearInterval(iv); setRunning(false); setDone(true); return 100 }
        return p + 2
      })
    }, 100)
  }

  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>Benchmark Runner</div>
        <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>Configure and execute performance benchmarks</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16 }}>
        <div className="flex flex-col gap-4">
          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-4">
            <SectionLabel>Configuration</SectionLabel>
            <div className="flex flex-col gap-2">
              <span style={{ fontSize: 13, color: t.textDim }}>Model</span>
              <select value={selectedModel} onChange={e => setSelectedModel(e.target.value)}
                style={{ background: t.inputBg, border: `1px solid ${t.borderInput}`, borderRadius: 5, color: t.text, padding: '8px 12px', fontSize: 13, outline: 'none' }}>
                {models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            </div>
            <Slider label="Concurrency" value={concurrency} min={1} max={32} step={1} onChange={setConcurrency} />
            <Slider label="Duration" value={duration} min={10} max={300} step={10} onChange={setDuration} unit="s" />
            <div className="flex flex-col gap-3">
              <SectionLabel>Prompt Strategy</SectionLabel>
              {['Fixed prompt (128 tokens)', 'Random synthetic prompts', 'Custom prompt file'].map((opt, i) => (
                <label key={opt} style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13, color: t.textDim, cursor: 'pointer' }}>
                  <input type="radio" name="prompt" defaultChecked={i === 0} style={{ accentColor: t.orange }} />
                  {opt}
                </label>
              ))}
            </div>
            <Btn variant="primary" onClick={runBenchmark} disabled={running}>
              {running ? `Running... ${progress}%` : '▶ Start Benchmark'}
            </Btn>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <SectionLabel>Progress</SectionLabel>
              {done && <Badge color={t.green}>COMPLETE</Badge>}
              {running && <Badge color={t.orange}>RUNNING</Badge>}
            </div>
            <div style={{ background: t.progressTrack, borderRadius: 4, height: 8, overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 4,
                width: `${progress}%`,
                background: `linear-gradient(90deg, ${t.orange}, ${t.cyan})`,
                transition: 'width 0.1s linear',
              }} />
            </div>
            <div style={{ fontSize: 12, color: t.textSecondary, fontFamily: 'JetBrains Mono, monospace' }}>
              {running ? `${Math.floor(progress * duration / 100)}s / ${duration}s elapsed` : done ? `Completed in ${duration}s` : 'Ready to run'}
            </div>
          </div>

          {(running || done) && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
              <MetricCard label="TTFT" value="48" unit="ms" color={t.cyan} />
              <MetricCard label="Tokens/sec" value="34.7" color={t.green} />
              <MetricCard label="P95 Latency" value="104" unit="ms" color={t.orange} />
            </div>
          )}

          <ChartCard title="CPU Utilization (%)">
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={cpuData}>
                <defs>
                  <linearGradient id="gcpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={t.divider} />
                <XAxis dataKey="t" tick={{ fill: t.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: t.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: t.tooltipBg, border: `1px solid ${t.border}`, borderRadius: 6, fontSize: 12 }} />
                <Area type="monotone" dataKey="cpu" stroke="#f97316" fill="url(#gcpu)" strokeWidth={2} name="CPU %" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          {done && (
            <ChartCard title="Before vs After — Key Metrics">
              <div className="flex flex-col gap-3">
                {comparisonData.map(m => {
                  const better = m.lowerBetter ? m.after < m.before : m.after > m.before
                  const pct = m.lowerBetter
                    ? Math.round((1 - m.after / m.before) * 100)
                    : Math.round((m.after / m.before - 1) * 100)
                  return (
                    <div key={m.label}>
                      <div className="flex justify-between items-center" style={{ marginBottom: 6 }}>
                        <span style={{ fontSize: 12, color: t.textDim }}>{m.label}</span>
                        <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: better ? t.green : t.red }}>
                          {better ? '↓' : '↑'} {pct}%
                        </span>
                      </div>
                      <div className="flex gap-2 items-center" style={{ fontSize: 11, color: t.textSecondary, fontFamily: 'JetBrains Mono, monospace' }}>
                        <span style={{ minWidth: 60 }}>Before: {m.before}{m.unit}</span>
                        <div style={{ flex: 1, height: 6, background: t.progressTrack, borderRadius: 3, position: 'relative' }}>
                          <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', borderRadius: 3, background: t.orange, width: `${(m.before / Math.max(m.before, m.after)) * 100}%` }} />
                        </div>
                        <span style={{ minWidth: 60, textAlign: 'right' }}>After: {m.after}{m.unit}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </ChartCard>
          )}
        </div>
      </div>
    </div>
  )
}

function Optimization() {
  const [quantization, setQuantization] = useState('INT4')
  const [batchSize, setBatchSize] = useState(8)
  const [threads, setThreads] = useState(32)
  const [kvCache, setKvCache] = useState(true)
  const [cpuAffinity, setCpuAffinity] = useState(true)
  const [numa, setNuma] = useState(false)
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)

  function runOptimization() {
    setRunning(true)
    setProgress(0)
    const iv = setInterval(() => {
      setProgress(p => {
        if (p >= 100) { clearInterval(iv); setRunning(false); return 100 }
        return p + 1
      })
    }, 80)
  }

  const quantOptions = ['FP32', 'BF16', 'FP16', 'INT8', 'INT4']

  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>Optimization Engine</div>
        <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>Tune quantization, threading, memory, and Arm-specific parameters</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <SectionLabel>Quantization</SectionLabel>
          <div className="flex gap-2 flex-wrap">
            {quantOptions.map(q => (
              <button key={q} onClick={() => setQuantization(q)} style={{
                padding: '7px 16px', borderRadius: 5, fontSize: 12, fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, cursor: 'pointer',
                background: quantization === q ? t.orange : t.ghostBg,
                color: quantization === q ? t.opaqueTextOnOrange : t.textDim,
                border: quantization === q ? 'none' : `1px solid ${t.borderInput}`,
                transition: 'all 0.15s',
              }}>{q}</button>
            ))}
          </div>
          <div style={{ background: t.innerSurface, borderRadius: 5, padding: '12px 14px', fontSize: 12, color: t.textDim, lineHeight: 1.6, transition: 'background 0.3s' }}>
            {quantization === 'INT4' && '4-bit integer quantization. ~2× memory reduction. Best throughput on Arm. Minimal quality degradation for most tasks.'}
            {quantization === 'INT8' && '8-bit integer quantization. Balanced memory/quality tradeoff. Good for production workloads.'}
            {quantization === 'FP16' && '16-bit float. Baseline performance. Full model quality. Higher memory usage.'}
            {quantization === 'BF16' && 'BFloat16 — native Arm Neoverse format. Better dynamic range than FP16. Recommended baseline.'}
            {quantization === 'FP32' && 'Full precision. Maximum quality. 2× memory vs FP16. Not recommended for inference.'}
          </div>
        </div>

        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-5">
          <SectionLabel>Compute Configuration</SectionLabel>
          <Slider label="Batch Size" value={batchSize} min={1} max={64} step={1} onChange={setBatchSize} />
          <Slider label="Thread Count" value={threads} min={1} max={64} step={1} onChange={setThreads} />
        </div>

        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <SectionLabel>Arm-Specific Optimizations</SectionLabel>
          {[
            { label: 'CPU Affinity Pinning', sub: 'Pin threads to physical cores, avoid SMT', val: cpuAffinity, set: setCpuAffinity },
            { label: 'KV Cache Optimization', sub: 'Quantized KV cache (Q8_0), reduces memory pressure', val: kvCache, set: setKvCache },
            { label: 'NUMA-Aware Scheduling', sub: 'Distribute memory across NUMA nodes', val: numa, set: setNuma },
          ].map(({ label, sub, val, set }) => (
            <div key={label} className="flex justify-between items-start" style={{ borderBottom: `1px solid ${t.rowDivider}`, paddingBottom: 12 }}>
              <div>
                <div style={{ fontSize: 13, color: t.text, fontWeight: 500 }}>{label}</div>
                <div style={{ fontSize: 11, color: t.textSecondary, marginTop: 3 }}>{sub}</div>
              </div>
              <Toggle value={val} onChange={set} />
            </div>
          ))}
          <div>
            <SectionLabel>Runtime</SectionLabel>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 10 }}>
              {['llama.cpp', 'ExecuTorch', 'ONNX Runtime', 'TensorRT-LLM'].map(rt => (
                <button key={rt} style={{
                  padding: '8px', borderRadius: 5, fontSize: 12, cursor: 'pointer', textAlign: 'center',
                  background: rt === 'llama.cpp' ? t.navActive : t.ghostBg,
                  border: rt === 'llama.cpp' ? `1px solid ${t.orange}40` : `1px solid ${t.border}`,
                  color: rt === 'llama.cpp' ? t.orange : t.textDim,
                  fontFamily: 'JetBrains Mono, monospace',
                }}>{rt}</button>
              ))}
            </div>
          </div>
        </div>

        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <SectionLabel>Estimated Impact</SectionLabel>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { label: 'Memory Reduction', value: '−53%', color: t.green },
              { label: 'Throughput Gain', value: '+169%', color: t.green },
              { label: 'TTFT Improvement', value: '−62%', color: t.cyan },
              { label: 'Quality Loss', value: '<1%', color: t.yellow },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: t.innerSurface, borderRadius: 5, padding: '12px 14px', transition: 'background 0.3s' }}>
                <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color, fontFamily: 'JetBrains Mono, monospace', marginTop: 6 }}>{value}</div>
              </div>
            ))}
          </div>

          {running && (
            <div className="flex flex-col gap-2">
              <div style={{ fontSize: 12, color: t.textSecondary, fontFamily: 'JetBrains Mono, monospace' }}>Optimizing... {progress}%</div>
              <div style={{ background: t.progressTrack, borderRadius: 4, height: 6, overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: 4, background: `linear-gradient(90deg, ${t.orange}, ${t.cyan})`, width: `${progress}%`, transition: 'width 0.1s' }} />
              </div>
            </div>
          )}

          <Btn variant="primary" onClick={runOptimization} disabled={running}>
            {running ? `Running Optimization... ${progress}%` : '⚡ Run Optimization'}
          </Btn>
        </div>
      </div>
    </div>
  )
}

function Recommendations() {
  const [applied, setApplied] = useState(false)

  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>AI Recommendations</div>
        <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>Automated analysis and configuration suggestions</div>
      </div>

      <div style={{ background: t.cardBg, border: `1px solid ${t.red}30`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: t.red, animation: 'pulse-dot 1.5s ease infinite' }} />
          <SectionLabel>Detected Bottleneck</SectionLabel>
        </div>
        <div style={{ fontSize: 14, color: t.text, lineHeight: 1.6 }}>
          Memory bandwidth saturation detected at <span style={{ color: t.orange, fontFamily: 'JetBrains Mono, monospace' }}>92.4% utilization</span>.
          FP16 weights are causing excessive memory traffic on the N1 interconnect.
          KV cache is consuming <span style={{ color: t.orange, fontFamily: 'JetBrains Mono, monospace' }}>4.2 GB</span> of working set.
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Badge color={t.red}>High Memory Pressure</Badge>
          <Badge color={t.yellow}>Suboptimal Thread Affinity</Badge>
          <Badge color={t.orange}>FP16 → INT4 Candidate</Badge>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <SectionLabel>Current Configuration</SectionLabel>
            <Badge color={t.textSecondary}>ACTIVE</Badge>
          </div>
          {[
            ['Model', 'Llama-3.2-3B'],
            ['Quantization', 'FP16'],
            ['Batch Size', '1'],
            ['Threads', '8'],
            ['CPU Affinity', 'Disabled'],
            ['KV Cache', 'Default (FP16)'],
            ['Runtime', 'llama.cpp v0.2'],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between" style={{ fontSize: 12, borderBottom: `1px solid ${t.rowDivider}`, paddingBottom: 8 }}>
              <span style={{ color: t.textSecondary }}>{k}</span>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', color: t.textDim }}>{v}</span>
            </div>
          ))}
        </div>

        <div style={{ background: t.cardBg, border: `1px solid ${t.green}30`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <SectionLabel>Recommended Configuration</SectionLabel>
            <Badge color={t.green}>+169% TPS</Badge>
          </div>
          {[
            ['Model', 'Llama-3.2-3B', ''],
            ['Quantization', 'INT4 (GGUF Q4_K_M)', t.green],
            ['Batch Size', '8', t.green],
            ['Threads', '32 (pinned)', t.green],
            ['CPU Affinity', 'NUMA-aware', t.green],
            ['KV Cache', 'Quantized Q8_0', t.green],
            ['Runtime', 'llama.cpp v0.3.8', t.green],
          ].map(([k, v, c]) => (
            <div key={k} className="flex justify-between" style={{ fontSize: 12, borderBottom: `1px solid ${t.rowDivider}`, paddingBottom: 8 }}>
              <span style={{ color: t.textSecondary }}>{k}</span>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', color: c || t.textDim }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
        <SectionLabel>Reasoning</SectionLabel>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
          {[
            { title: 'INT4 Quantization', reason: 'Reduces model memory footprint from 6.4 GB to 2.1 GB. Arm NEON SIMD units can process 4-bit ops natively via Q4_K_M GGUF format. Quality perplexity delta: +0.42 (negligible).', impact: '−67% memory', color: t.cyan },
            { title: 'Batch Size 8', reason: 'N1 core complex achieves peak throughput at batch=8 given available L3 cache (32 MB). Higher batches increase cache thrashing. Lower batches under-utilize vector units.', impact: '+3.1× throughput', color: t.green },
            { title: 'CPU Affinity', reason: 'Pinning 32 inference threads to physical cores 0-31 eliminates context switch overhead and improves L1/L2 cache locality. Estimated 12-18% latency reduction.', impact: '−15% TTFT', color: t.orange },
          ].map(({ title, reason, impact, color }) => (
            <div key={title} style={{ background: t.innerSurface, borderRadius: 5, padding: '14px', transition: 'background 0.3s' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color, marginBottom: 8 }}>{title}</div>
              <div style={{ fontSize: 12, color: t.textSecondary, lineHeight: 1.6, marginBottom: 10 }}>{reason}</div>
              <Badge color={color}>{impact}</Badge>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 10 }}>
        {comparisonData.map(m => {
          const better = m.lowerBetter ? m.after < m.before : m.after > m.before
          const pct = m.lowerBetter
            ? Math.round((1 - m.after / m.before) * 100)
            : Math.round((m.after / m.before - 1) * 100)
          return (
            <div key={m.label} style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-4 flex flex-col gap-1.5">
              <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{m.label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: better ? t.green : t.red }}>
                {better ? '↓' : '↑'}{pct}%
              </div>
              <div style={{ fontSize: 11, color: t.textSecondary, fontFamily: 'JetBrains Mono, monospace' }}>
                {m.before}{m.unit} → {m.after}{m.unit}
              </div>
            </div>
          )
        })}
      </div>

      <div className="flex gap-3">
        {!applied ? (
          <Btn variant="primary" onClick={() => setApplied(true)}>⚡ Apply Recommendation</Btn>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: t.green }}>
            <span>✓</span> Configuration applied successfully
          </div>
        )}
        <Btn variant="ghost">Export Config JSON</Btn>
      </div>
    </div>
  )
}

function Reports() {
  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div className="flex items-center justify-between">
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>Performance Report</div>
          <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>RUN-0042 · Llama-3.2-3B · 2026-08-11 14:32 UTC</div>
        </div>
        <div className="flex gap-2">
          <Btn variant="ghost" small>Export Markdown</Btn>
          <Btn variant="ghost" small>Export HTML</Btn>
          <Btn variant="primary" small>Export PDF</Btn>
        </div>
      </div>

      <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
        <SectionLabel>Executive Summary</SectionLabel>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[
            { label: 'OVERALL IMPROVEMENT', value: '+169%', sub: 'Throughput gain vs FP16 baseline', color: t.green },
            { label: 'MEMORY REDUCTION', value: '−53%', sub: '6.4 GB → 3.2 GB working set', color: t.cyan },
            { label: 'LATENCY (P95)', value: '−66%', sub: '310ms → 104ms', color: t.orange },
          ].map(({ label, value, sub, color }) => (
            <div key={label} style={{ background: t.innerSurface, borderRadius: 5, padding: '14px', transition: 'background 0.3s' }}>
              <div style={{ fontSize: 11, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', marginBottom: 6 }}>{label}</div>
              <div style={{ fontSize: 32, fontWeight: 700, color, fontFamily: 'JetBrains Mono, monospace' }}>{value}</div>
              <div style={{ fontSize: 12, color: t.textSecondary, marginTop: 4 }}>{sub}</div>
            </div>
          ))}
        </div>
      </div>

      <ChartCard title="Before vs After — Throughput (tokens/sec)">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={[
            { name: 'FP16 Baseline', value: 12.9 },
            { name: 'INT4 + Optimized', value: 34.7 },
          ]} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke={t.divider} horizontal={false} />
            <XAxis type="number" tick={{ fill: t.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" tick={{ fill: t.textDim, fontSize: 12 }} axisLine={false} tickLine={false} width={140} />
            <Tooltip contentStyle={{ background: t.tooltipBg, border: `1px solid ${t.border}`, borderRadius: 6, fontSize: 12 }} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} fill="#f97316" />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Detailed Metrics — Before vs After">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${t.divider}` }}>
              {['Metric', 'Baseline (FP16)', 'Optimized (INT4)', 'Delta', 'Status'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '0 12px 10px 0', fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              { metric: 'TTFT', before: '127 ms', after: '48 ms', delta: '−62%', good: true },
              { metric: 'Tokens/sec', before: '12.9', after: '34.7', delta: '+169%', good: true },
              { metric: 'P50 Latency', before: '82 ms', after: '62 ms', delta: '−24%', good: true },
              { metric: 'P95 Latency', before: '310 ms', after: '104 ms', delta: '−66%', good: true },
              { metric: 'P99 Latency', before: '481 ms', after: '162 ms', delta: '−66%', good: true },
              { metric: 'Memory Usage', before: '6.4 GB', after: '3.2 GB', delta: '−50%', good: true },
              { metric: 'CPU Utilization', before: '91%', after: '84%', delta: '−7pp', good: true },
              { metric: 'Model Size', before: '6.4 GB', after: '2.1 GB', delta: '−67%', good: true },
            ].map((r, i) => (
              <tr key={r.metric} style={{ borderBottom: i < 7 ? `1px solid ${t.rowDivider}` : 'none' }}>
                <td style={{ padding: '10px 12px 10px 0', fontSize: 13, color: t.text }}>{r.metric}</td>
                <td style={{ padding: '10px 12px 10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.textDim }}>{r.before}</td>
                <td style={{ padding: '10px 12px 10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.text }}>{r.after}</td>
                <td style={{ padding: '10px 12px 10px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: r.good ? t.green : t.red }}>{r.delta}</td>
                <td style={{ padding: '10px 12px 10px 0' }}>
                  <Badge color={t.green}>IMPROVED</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </ChartCard>

      <ChartCard title="Optimization Details">
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.textSecondary, lineHeight: 1.8 }}>
          {[
            ['model', 'Llama-3.2-3B (Meta)'],
            ['runtime', 'llama.cpp v0.3.8 (Arm NEON + SVE2)'],
            ['quantization', 'Q4_K_M GGUF (INT4)'],
            ['threads', '32 (pinned, cores 0-31)'],
            ['batch_size', '8'],
            ['kv_cache', 'quantized Q8_0'],
            ['cpu_affinity', 'NUMA-aware, socket 0'],
            ['platform', 'Arm Neoverse N1 · 64-core · 128 GB'],
            ['duration', '60s · 1,200 requests'],
            ['timestamp', '2026-08-11T14:32:18Z'],
          ].map(([k, v]) => (
            <div key={k}><span style={{ color: t.orange }}>{k}:</span> {v}</div>
          ))}
        </div>
      </ChartCard>
    </div>
  )
}

function History() {
  const [selected, setSelected] = useState<string[]>([])

  function toggle(id: string) {
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : s.length < 2 ? [...s, id] : s)
  }

  const allRuns = [
    ...benchmarkRuns,
    { id: 'RUN-0037', model: 'Gemma-2B', config: 'INT4 + batch=4', ttft: '22ms', tps: '67.4', p95: '52ms', status: 'pass' },
    { id: 'RUN-0036', model: 'Qwen2.5-7B', config: 'INT8 + batch=2', ttft: '98ms', tps: '22.1', p95: '218ms', status: 'pass' },
    { id: 'RUN-0035', model: 'Phi-3-mini', config: 'FP16 baseline', ttft: '84ms', tps: '19.7', p95: '201ms', status: 'pass' },
  ]

  const { t } = useTheme()
  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div className="flex items-center justify-between">
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>Run History</div>
          <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>Select up to 2 runs to compare</div>
        </div>
        {selected.length === 2 && <Btn variant="cyan">Compare Selected →</Btn>}
      </div>

      <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${t.divider}` }}>
              {['', 'Run ID', 'Model', 'Configuration', 'TTFT', 'Tokens/sec', 'P95', 'Status', 'Date'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '0 12px 12px 0', fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allRuns.map((r, i) => {
              const isSelected = selected.includes(r.id)
              return (
                <tr key={r.id} onClick={() => toggle(r.id)} style={{
                  borderBottom: i < allRuns.length - 1 ? `1px solid ${t.rowDivider}` : 'none',
                  cursor: 'pointer',
                  background: isSelected ? `${t.orange}08` : 'transparent',
                  transition: 'background 0.15s',
                }}>
                  <td style={{ padding: '11px 12px 11px 0' }}>
                    <div style={{
                      width: 16, height: 16, borderRadius: 3,
                      border: isSelected ? 'none' : `1px solid ${t.ghostBorder}`,
                      background: isSelected ? t.orange : 'transparent',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {isSelected && <span style={{ fontSize: 10, color: t.opaqueTextOnOrange, fontWeight: 700 }}>✓</span>}
                    </div>
                  </td>
                  <td style={{ padding: '11px 12px 11px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.cyan }}>{r.id}</td>
                  <td style={{ padding: '11px 12px 11px 0', fontSize: 13, color: t.text }}>{r.model}</td>
                  <td style={{ padding: '11px 12px 11px 0', fontSize: 12, color: t.textDim }}>{r.config}</td>
                  <td style={{ padding: '11px 12px 11px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.text }}>{r.ttft}</td>
                  <td style={{ padding: '11px 12px 11px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.green }}>{r.tps}</td>
                  <td style={{ padding: '11px 12px 11px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.text }}>{r.p95}</td>
                  <td style={{ padding: '11px 12px 11px 0' }}>
                    <Badge color={r.status === 'pass' ? t.green : t.red}>{r.status.toUpperCase()}</Badge>
                  </td>
                  <td style={{ padding: '11px 0 11px 0', fontSize: 12, color: t.textSecondary }}>2026-08-{String(11 - i).padStart(2, '0')}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Settings({ onSignOut }: { onSignOut?: () => void }) {
  const { t, isDark, setIsDark } = useTheme()
  const [apiUrl, setApiUrl] = useState('http://localhost:8080')
  const [apiKey, setApiKey] = useState('arm-pilot-••••••••••••••••')
  const [autoOpt, setAutoOpt] = useState(false)
  const [telemetry, setTelemetry] = useState(true)

  return (
    <div className="flex flex-col gap-6 animate-slide-in">
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading }}>Settings</div>
        <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 4 }}>API, system, and account configuration</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <SectionLabel>API Settings</SectionLabel>
          {[
            { label: 'Inference Server URL', value: apiUrl, set: setApiUrl },
            { label: 'API Key', value: apiKey, set: setApiKey },
          ].map(({ label, value, set }) => (
            <div key={label} className="flex flex-col gap-2">
              <span style={{ fontSize: 13, color: t.textDim }}>{label}</span>
              <input value={value} onChange={e => set(e.target.value)} style={{
                background: t.inputBg, border: `1px solid ${t.borderInput}`, borderRadius: 5,
                color: t.text, padding: '9px 12px', fontSize: 13, outline: 'none',
                fontFamily: 'JetBrains Mono, monospace',
              }} />
            </div>
          ))}
          <Btn variant="ghost" small>Test Connection</Btn>
        </div>

        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <SectionLabel>System Configuration</SectionLabel>
          {[
            { label: 'Dark Mode', sub: 'Use dark color scheme', val: isDark, set: (v: boolean) => setIsDark(v) },
            { label: 'Auto-Optimization', sub: 'Run optimization after each benchmark', val: autoOpt, set: setAutoOpt },
            { label: 'Telemetry', sub: 'Send anonymous performance data', val: telemetry, set: setTelemetry },
          ].map(({ label, sub, val, set }) => (
            <div key={label} className="flex justify-between items-center" style={{ borderBottom: `1px solid ${t.rowDivider}`, paddingBottom: 12 }}>
              <div>
                <div style={{ fontSize: 13, color: t.text, fontWeight: 500 }}>{label}</div>
                <div style={{ fontSize: 11, color: t.textSecondary, marginTop: 2 }}>{sub}</div>
              </div>
              <Toggle value={val} onChange={set} />
            </div>
          ))}
        </div>

        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-3">
          <SectionLabel>Platform Information</SectionLabel>
          {[
            ['CPU', 'Arm Neoverse N1 · 64-core'],
            ['Memory', '128 GB DDR4-3200'],
            ['OS', 'Ubuntu 24.04 LTS (aarch64)'],
            ['Kernel', 'Linux 6.8.0-arm64'],
            ['ArmPilot', 'v2.4.1'],
            ['llama.cpp', 'v0.3.8 (b3490)'],
            ['GGUF', 'v3'],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between" style={{ fontSize: 12, borderBottom: `1px solid ${t.rowDivider}`, paddingBottom: 8 }}>
              <span style={{ color: t.textSecondary }}>{k}</span>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', color: t.text }}>{v}</span>
            </div>
          ))}
        </div>

        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, transition: 'background 0.3s' }} className="p-5 flex flex-col gap-4">
          <SectionLabel>Account</SectionLabel>
          <div className="flex items-center gap-4">
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: `linear-gradient(135deg, ${t.orange}, ${t.cyan})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: '#fff' }}>
              A
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: t.text }}>ArmPilot Admin</div>
              <div style={{ fontSize: 12, color: t.textSecondary }}>admin@armpilot.dev</div>
            </div>
          </div>
          <div className="flex gap-2">
            <Btn variant="ghost" small>Change Password</Btn>
            <Btn variant="danger" small onClick={onSignOut}>Sign Out</Btn>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Landing Page ────────────────────────────────────────────────────────────

function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: Math.round(size * 0.22),
      background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.5, fontWeight: 800, color: '#fff', flexShrink: 0,
    }}>A</div>
  )
}

function LandingPage({ onNav }: { onNav: (tab: AuthTab) => void }) {
  const [scrolled, setScrolled] = useState(false)
  const { t, isDark, setIsDark } = useTheme()
  const reportRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handler)
    return () => window.removeEventListener('scroll', handler)
  }, [])

  function scrollToReport() {
    reportRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const OrangeBtn = ({ children, onClick, large }: { children: React.ReactNode; onClick?: () => void; large?: boolean }) => (
    <button onClick={onClick} style={{
      background: '#f97316', border: 'none', borderRadius: 6,
      color: isDark ? '#0b0e14' : '#fff', fontSize: large ? 15 : 13, fontWeight: 700,
      padding: large ? '14px 36px' : '8px 18px', cursor: 'pointer',
      transition: 'background 0.15s', whiteSpace: 'nowrap',
    }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#fb923c' }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#f97316' }}
    >{children}</button>
  )

  const GhostBtn = ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick} style={{
      background: t.ghostBg, border: `1px solid ${t.ghostBorder}`,
      borderRadius: 6, color: t.text, fontSize: 13, fontWeight: 500,
      padding: '8px 18px', cursor: 'pointer', transition: 'background 0.15s', whiteSpace: 'nowrap',
    }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBgHover }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBg }}
    >{children}</button>
  )

  return (
    <div style={{ background: t.bg, minHeight: '100vh', color: t.text, fontFamily: 'Inter, sans-serif', transition: 'background 0.3s, color 0.3s' }}>

      {/* ── Header ── */}
      <header style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        background: scrolled ? t.scrolledHeaderBg : 'transparent',
        borderBottom: scrolled ? `1px solid ${t.border}` : '1px solid transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        transition: 'background 0.3s, border-color 0.3s',
        padding: '0 48px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <LogoMark size={30} />
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: t.text, letterSpacing: '-0.02em' }}>ArmPilot</div>
            <div style={{ fontSize: 9, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', lineHeight: 1 }}>AI · v2.4.1</div>
          </div>
        </div>
        <nav style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          {['Product', 'How It Works', 'Benchmarks', 'Docs'].map(l => (
            <a key={l} href="#" style={{ fontSize: 13, color: t.textSecondary, textDecoration: 'none', transition: 'color 0.15s' }}
              onMouseEnter={e => (e.currentTarget.style.color = t.text)}
              onMouseLeave={e => (e.currentTarget.style.color = t.textSecondary)}>{l}</a>
          ))}
          <div style={{ width: 1, height: 16, background: t.border }} />
          {/* ── Theme toggle ── */}
          <button
            onClick={() => setIsDark(d => !d)}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            style={{
              background: t.ghostBg, border: `1px solid ${t.ghostBorder}`, borderRadius: 5,
              color: t.text, width: 34, height: 34, display: 'flex', alignItems: 'center',
              justifyContent: 'center', cursor: 'pointer', fontSize: 15, flexShrink: 0,
              transition: 'background 0.15s, border-color 0.15s',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBgHover }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBg }}
          >
            {isDark ? '☀' : '☾'}
          </button>
          <button onClick={() => onNav('login')} style={{
            background: 'transparent', border: `1px solid ${t.ghostBorder}`, borderRadius: 5,
            color: t.text, fontSize: 13, fontWeight: 500, padding: '7px 16px', cursor: 'pointer',
            transition: 'border-color 0.15s',
          }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = t.ghostBorderHover }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = t.ghostBorder }}
          >Log In</button>
          <OrangeBtn onClick={() => onNav('signup')}>Get Started</OrangeBtn>
        </nav>
      </header>

      {/* ── Hero ── */}
      <section style={{ paddingTop: 140, paddingBottom: 60, textAlign: 'center', maxWidth: 760, margin: '0 auto', padding: '140px 32px 60px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 24,
          background: 'rgba(249,115,22,0.1)', border: '1px solid rgba(249,115,22,0.25)',
          borderRadius: 4, padding: '4px 12px',
        }}>
          <span style={{ fontSize: 10, color: '#f97316', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.12em', textTransform: 'uppercase' }}>ARM64-FIRST INFERENCE</span>
        </div>
        <h1 style={{ fontSize: 54, fontWeight: 800, lineHeight: 1.1, letterSpacing: '-0.03em', color: t.textHeading, margin: '0 0 20px' }}>
          Stop guessing your LLM config.<br />
          <span style={{ color: '#f97316' }}>Let ArmPilot find it.</span>
        </h1>
        <p style={{ fontSize: 17, color: t.textSecondary, lineHeight: 1.7, margin: '0 auto 36px', maxWidth: 580 }}>
          Deploy open-source LLMs on Arm64 cloud infrastructure, automatically benchmark them, and get the best configuration for latency, throughput, or cost — no manual trial and error.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <OrangeBtn onClick={() => onNav('signup')} large>Get Started Free →</OrangeBtn>
          <button onClick={scrollToReport} style={{
            background: t.ghostBg, border: `1px solid ${t.ghostBorder}`,
            borderRadius: 6, color: t.text, fontSize: 15, fontWeight: 500, padding: '13px 28px', cursor: 'pointer',
            transition: 'background 0.15s',
          }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBgHover }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBg }}
          >See a Benchmark Report</button>
        </div>
      </section>

      {/* ── Dashboard mockup ── */}
      <section style={{ padding: '0 48px 80px', maxWidth: 1160, margin: '0 auto' }}>
        <div style={{
          border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10,
          overflow: 'hidden', boxShadow: '0 40px 100px rgba(0,0,0,0.6)',
          background: '#0e1218',
        }}>
          <div style={{ height: 40, background: '#0e1218', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', padding: '0 16px', gap: 6 }}>
            {['#ef4444', '#eab308', '#22c55e'].map(c => (
              <span key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c, opacity: 0.7 }} />
            ))}
            <div style={{ marginLeft: 12, flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: 4, height: 22, maxWidth: 280, display: 'flex', alignItems: 'center', padding: '0 10px' }}>
              <span style={{ fontSize: 10, color: '#475569', fontFamily: 'JetBrains Mono, monospace' }}>app.armpilot.dev/dashboard</span>
            </div>
          </div>
          <div style={{ display: 'flex', height: 380 }}>
            <div style={{ width: 52, background: '#0e1218', borderRight: '1px solid rgba(255,255,255,0.06)', padding: '12px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ width: 32, height: 32, borderRadius: 7, background: 'linear-gradient(135deg, #f97316, #ea580c)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 800, color: '#fff', marginBottom: 8 }}>A</div>
              {['⬛', '◈', '◉', '⚡', '✦'].map((icon, i) => (
                <div key={i} style={{ width: 32, height: 28, borderRadius: 5, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, background: i === 0 ? 'rgba(249,115,22,0.15)' : 'transparent', color: i === 0 ? '#f97316' : '#334155' }}>{icon}</div>
              ))}
            </div>
            <div style={{ flex: 1, padding: 16, overflow: 'hidden' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 12 }}>
                {[
                  { label: 'TTFT', val: '48', unit: 'ms', color: '#06b6d4', trend: '−62%' },
                  { label: 'TOKENS/SEC', val: '34.7', color: '#22c55e', trend: '+169%' },
                  { label: 'P95 LATENCY', val: '104', unit: 'ms', color: '#f97316', trend: '−66%' },
                  { label: 'THROUGHPUT', val: '2,840', unit: 'tok/min', color: '#a78bfa', trend: '+2.7×' },
                ].map(({ label, val, unit, color, trend }) => (
                  <div key={label} style={{ background: '#141820', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 5, padding: '10px 12px' }}>
                    <div style={{ fontSize: 8, color: '#475569', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.08em', marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color, fontFamily: 'JetBrains Mono, monospace', lineHeight: 1 }}>{val}<span style={{ fontSize: 9, color: '#64748b', marginLeft: 2 }}>{unit}</span></div>
                    <div style={{ fontSize: 9, color: '#22c55e', fontFamily: 'JetBrains Mono, monospace', marginTop: 3 }}>{trend}</div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  { title: 'Throughput — Before vs After', lines: [{ pts: '0,60 30,55 60,50 90,40 120,35 150,28 200,22', color: '#22c55e' }, { pts: '0,70 30,65 60,68 90,60 120,55 150,52 200,48', color: '#f97316', dash: true }] },
                  { title: 'Latency Distribution (ms)', lines: [{ pts: '0,20 30,22 60,25 90,28 120,30 150,35 200,38', color: '#ef4444' }, { pts: '0,38 30,40 60,44 90,48 120,52 150,54 200,58', color: '#f97316' }, { pts: '0,58 30,60 60,63 90,65 120,68 150,70 200,72', color: '#06b6d4' }] },
                ].map(({ title, lines }) => (
                  <div key={title} style={{ background: '#141820', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 5, padding: '10px 12px', height: 140 }}>
                    <div style={{ fontSize: 8, color: '#475569', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.08em', marginBottom: 8, textTransform: 'uppercase' }}>{title}</div>
                    <svg width="100%" height="80" viewBox="0 0 200 80" preserveAspectRatio="none">
                      {lines.map((l, i) => <polyline key={i} points={l.pts} fill="none" stroke={l.color} strokeWidth="1.5" strokeDasharray={'dash' in l && l.dash ? '3,2' : undefined} />)}
                    </svg>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 11, color: t.textFaint, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.08em' }}>
          SYSTEM OVERVIEW · AWS GRAVITON3 · 64-CORE · 128 GB
        </div>
      </section>

      {/* ── Problem strip ── */}
      <section style={{ padding: '0 48px 72px', maxWidth: 1000, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {[
            { label: 'BATCH SIZE', icon: '?', q: 'Which batch size?', note: "Developers don't know the optimal batch size for their hardware — and wrong guesses tank throughput." },
            { label: 'QUANTIZATION', icon: '÷', q: 'Quantize or not?', note: 'Unclear when INT8/INT4 actually helps vs hurts — depends on model, hardware, and workload type.' },
            { label: 'WASTED COST', icon: '$', q: "Paying for compute you don't use?", note: 'Wrong configs mean burning Graviton hours for a fraction of potential throughput.' },
          ].map(({ label, icon, q, note }) => (
            <div key={label} style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, padding: '20px 20px 22px', transition: 'background 0.3s' }}>
              <div style={{ fontSize: 9, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 14 }}>{label}</div>
              <div style={{ fontSize: 20, color: t.red, fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, marginBottom: 10 }}>{icon}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: t.text, marginBottom: 8 }}>{q}</div>
              <div style={{ fontSize: 12, color: t.textSecondary, lineHeight: 1.65 }}>{note}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section style={{ borderTop: `1px solid ${t.divider}`, padding: '72px 48px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 10 }}>How It Works</div>
          <h2 style={{ fontSize: 34, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading, margin: 0 }}>From deploy to optimal config in 4 steps</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, position: 'relative' }}>
          {[
            { step: '01', label: 'DEPLOY', icon: '▶', color: t.cyan, title: 'Point at your model', desc: 'Connect ArmPilot to your open-source LLM running on any Arm64 instance — Graviton2, Graviton3, or Neoverse.' },
            { step: '02', label: 'BASELINE', icon: '◉', color: t.green, title: 'Automatic benchmarking', desc: 'ArmPilot measures TTFT, tokens/sec, throughput, P95 latency, and memory usage with zero config.' },
            { step: '03', label: 'OPTIMIZE', icon: '⚡', color: '#f97316', title: 'Sweep configurations', desc: 'Tests INT8/INT4 quantization, KV cache settings, batch size, thread count, and CPU affinity automatically.' },
            { step: '04', label: 'RECOMMEND', icon: '✦', color: t.purple, title: 'Best config delivered', desc: 'Get the winning setup for lowest latency, highest throughput, or best cost/performance — with a full before/after report.' },
          ].map(({ step, label, icon, color, title, desc }, i) => (
            <div key={step} style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, padding: '22px 20px', position: 'relative', transition: 'background 0.3s' }}>
              {i < 3 && (
                <div style={{ position: 'absolute', right: -7, top: '50%', transform: 'translateY(-50%)', zIndex: 2, width: 14, height: 14, background: t.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: t.textFaint }}>→</div>
              )}
              <div style={{ fontSize: 9, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 14 }}>{label}</div>
              <div style={{ fontSize: 28, fontWeight: 800, color, fontFamily: 'JetBrains Mono, monospace', lineHeight: 1, marginBottom: 6 }}>{step}</div>
              <div style={{ fontSize: 18, marginBottom: 10, color }}>{icon}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: t.text, marginBottom: 8, lineHeight: 1.3 }}>{title}</div>
              <div style={{ fontSize: 12, color: t.textSecondary, lineHeight: 1.65 }}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Feature grid ── */}
      <section style={{ padding: '72px 48px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 10 }}>Platform Capabilities</div>
          <h2 style={{ fontSize: 34, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading, margin: 0 }}>Built for Arm64 inference, end to end</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 }}>
          {[
            { label: 'OPTIMIZATION', icon: '⚡', color: '#f97316', title: 'Optimization Engine', desc: 'INT8/INT4 quantization, KV cache, batch size, thread count, and CPU affinity tuning — automated, not manual.' },
            { label: 'AI RECOMMEND', icon: '✦', color: t.purple, title: 'Recommendation Engine', desc: 'Rules-based picks for lowest latency, highest throughput, or best cost/performance — with reasoning.' },
            { label: 'REPORTS', icon: '▤', color: t.green, title: 'Before vs After Reports', desc: 'Auto-generated Markdown and HTML comparison reports you can share with your team or include in a PR.' },
            { label: 'INFERENCE', icon: '◈', color: t.cyan, title: 'OpenAI-Compatible API', desc: 'Swap your base URL and keep your existing app code. No SDK changes, no prompt rewrites.' },
          ].map(({ label, icon, color, title, desc }) => (
            <div key={label} style={{
              background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 6, padding: '20px 20px 22px',
              transition: 'border-color 0.2s, background 0.3s',
            }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = `${color}35`)}
              onMouseLeave={e => (e.currentTarget.style.borderColor = t.border)}
            >
              <div style={{ fontSize: 9, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 14 }}>{label}</div>
              <div style={{ fontSize: 22, marginBottom: 12, color }}>{icon}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: t.text, marginBottom: 8, lineHeight: 1.3 }}>{title}</div>
              <div style={{ fontSize: 12, color: t.textSecondary, lineHeight: 1.65 }}>{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── "What We're Not" ── */}
      <section style={{ padding: '0 48px 72px', maxWidth: 860, margin: '0 auto' }}>
        <div style={{
          borderLeft: '2px solid rgba(249,115,22,0.4)', paddingLeft: 20,
          display: 'flex', alignItems: 'flex-start', gap: 12,
        }}>
          <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 2, flexShrink: 0 }}>NOTE</div>
          <p style={{ margin: 0, fontSize: 14, color: t.textSecondary, lineHeight: 1.65 }}>
            ArmPilot isn&apos;t a full MLOps platform — it&apos;s laser-focused on one thing:{' '}
            <span style={{ color: t.highlightedText }}>Arm64-first inference optimization for open-source LLMs.</span>
          </p>
        </div>
      </section>

      {/* ── Benchmark report preview ── */}
      <div ref={reportRef} />
      <section style={{ borderTop: `1px solid ${t.divider}`, padding: '72px 48px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 10 }}>Benchmark Report</div>
          <h2 style={{ fontSize: 34, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading, margin: 0 }}>RUN-0042 · Llama-3.2-3B · INT4 vs FP16</h2>
        </div>
        <div style={{ background: t.cardBg, border: `1px solid ${t.border}`, borderRadius: 8, padding: '24px 28px', transition: 'background 0.3s' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginBottom: 20 }}>
            {[
              { label: 'OVERALL IMPROVEMENT', value: '+169%', sub: 'Throughput gain vs FP16 baseline', color: t.green },
              { label: 'MEMORY REDUCTION', value: '−53%', sub: '6.4 GB → 3.2 GB working set', color: t.cyan },
              { label: 'P95 LATENCY', value: '−66%', sub: '310 ms → 104 ms', color: '#f97316' },
            ].map(({ label, value, sub, color }) => (
              <div key={label} style={{ background: t.innerSurface, borderRadius: 6, padding: '16px 18px', transition: 'background 0.3s' }}>
                <div style={{ fontSize: 9, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>{label}</div>
                <div style={{ fontSize: 36, fontWeight: 800, color, fontFamily: 'JetBrains Mono, monospace', lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: 11, color: t.textSecondary, marginTop: 6 }}>{sub}</div>
              </div>
            ))}
          </div>
          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: t.textSecondary, lineHeight: 1.9, borderTop: `1px solid ${t.divider}`, paddingTop: 16 }}>
            {[
              ['model', 'Llama-3.2-3B (Meta)'],
              ['runtime', 'llama.cpp v0.3.8 (Arm NEON + SVE2)'],
              ['quantization', 'Q4_K_M GGUF (INT4)'],
              ['platform', 'AWS Graviton3 · 64-core · 128 GB'],
              ['timestamp', '2026-08-13T11:00:00Z'],
            ].map(([k, v]) => (
              <div key={k}><span style={{ color: '#f97316' }}>{k}:</span> {v}</div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Tech/compatibility strip ── */}
      <section style={{ borderTop: `1px solid ${t.divider}`, borderBottom: `1px solid ${t.divider}`, padding: '22px 48px' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 40, justifyContent: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 9, color: t.textFaint, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.12em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Built on</span>
          {['FastAPI', 'Hugging Face Transformers', 'ONNX Runtime', 'llama.cpp', 'Docker', 'AWS Graviton'].map(l => (
            <div key={l} style={{ fontSize: 12, color: t.textFaint, fontWeight: 500, whiteSpace: 'nowrap' }}>{l}</div>
          ))}
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section style={{ padding: '80px 48px', textAlign: 'center' }}>
        <div style={{ maxWidth: 560, margin: '0 auto' }}>
          <h2 style={{ fontSize: 34, fontWeight: 700, letterSpacing: '-0.02em', color: t.textHeading, margin: '0 0 16px' }}>
            Ready to stop guessing your LLM config?
          </h2>
          <p style={{ fontSize: 16, color: t.textSecondary, marginBottom: 32, lineHeight: 1.6 }}>
            Deploy in under 5 minutes on Graviton. No credit card required.
          </p>
          <OrangeBtn onClick={() => onNav('signup')} large>Get Started Free →</OrangeBtn>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ borderTop: `1px solid ${t.divider}`, padding: '28px 48px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <LogoMark size={22} />
          <span style={{ fontSize: 13, color: t.textFaint }}>© 2026 ArmPilot, Inc.</span>
        </div>
        <div style={{ display: 'flex', gap: 24 }}>
          {['Docs', 'GitHub', 'Contact'].map(l => (
            <a key={l} href="#" style={{ fontSize: 12, color: t.textFaint, textDecoration: 'none', transition: 'color 0.15s' }}
              onMouseEnter={e => (e.currentTarget.style.color = t.textSecondary)}
              onMouseLeave={e => (e.currentTarget.style.color = t.textFaint)}>{l}</a>
          ))}
        </div>
      </footer>
    </div>
  )
}

// ─── Auth Page ────────────────────────────────────────────────────────────────

function AuthPage({ defaultTab, onSuccess }: { defaultTab: AuthTab; onSuccess: (name?: string) => void }) {
  const { t } = useTheme()
  const [tab, setTab] = useState<AuthTab>(defaultTab)
  const [loading, setLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)

  // Login fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Signup fields
  const [name, setName] = useState('')
  const [signupEmail, setSignupEmail] = useState('')
  const [signupPass, setSignupPass] = useState('')
  const [agreed, setAgreed] = useState(false)

  const passStrength = signupPass.length === 0 ? 0 : signupPass.length < 6 ? 1 : signupPass.length < 10 ? 2 : 3
  const passColor = ['transparent', t.red, t.orange, t.green][passStrength]
  const passLabel = ['', 'Weak', 'Fair', 'Strong'][passStrength]

  function handleSubmit() {
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      onSuccess(tab === 'signup' ? name || undefined : undefined)
    }, 1400)
  }

  const inputStyle: React.CSSProperties = {
    width: '100%', background: t.inputBg, border: `1px solid ${t.borderInput}`,
    borderRadius: 5, color: t.text, padding: '10px 14px', fontSize: 13, outline: 'none',
    fontFamily: 'Inter, sans-serif', boxSizing: 'border-box', transition: 'border-color 0.15s, background 0.3s',
  }

  function SocialBtn({ icon, label }: { icon: string; label: string }) {
    return (
      <button style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        background: t.ghostBg, border: `1px solid ${t.ghostBorder}`,
        borderRadius: 5, padding: '9px 0', fontSize: 13, color: t.text, cursor: 'pointer',
        transition: 'background 0.15s',
      }}
        onMouseEnter={e => (e.currentTarget.style.background = t.ghostBgHover)}
        onMouseLeave={e => (e.currentTarget.style.background = t.ghostBg)}
      ><span style={{ fontSize: 16 }}>{icon}</span>{label}</button>
    )
  }

  return (
    <div style={{
      background: t.bg, minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', fontFamily: 'Inter, sans-serif', color: t.text, padding: '40px 16px',
      transition: 'background 0.3s, color 0.3s',
    }}>
      {/* Subtle radial glow behind card */}
      <div style={{ position: 'fixed', top: '40%', left: '50%', transform: 'translate(-50%,-50%)', width: 600, height: 600, background: 'radial-gradient(circle, rgba(249,115,22,0.06) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <div style={{ width: '100%', maxWidth: 420, position: 'relative' }}>
        {/* Logo above card */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
            <LogoMark size={44} />
            <div style={{ fontSize: 17, fontWeight: 700, color: t.text, letterSpacing: '-0.02em' }}>ArmPilot</div>
            <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace' }}>AI · v2.4.1</div>
          </div>
        </div>

        {/* Card */}
        <div style={{
          background: t.cardBg, border: `1px solid ${t.border}`,
          borderRadius: 8, padding: '28px 28px 24px', transition: 'background 0.3s',
        }}>

          {/* Tab switcher */}
          <div style={{ display: 'flex', marginBottom: 24, borderBottom: `1px solid ${t.divider}` }}>
            {(['login', 'signup'] as const).map(tabKey => (
              <button key={tabKey} onClick={() => setTab(tabKey)} style={{
                flex: 1, background: 'none', border: 'none', cursor: 'pointer',
                padding: '0 0 14px', fontSize: 14, fontWeight: tab === tabKey ? 600 : 400,
                color: tab === tabKey ? t.text : t.textSecondary,
                borderBottom: tab === tabKey ? '2px solid #f97316' : '2px solid transparent',
                marginBottom: -1, transition: 'color 0.15s, border-color 0.15s',
              }}>
                {tabKey === 'login' ? 'Log In' : 'Sign Up'}
              </button>
            ))}
          </div>

          {tab === 'login' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 12, color: t.textDim, display: 'block', marginBottom: 6 }}>Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" style={inputStyle}
                  onFocus={e => (e.target.style.borderColor = 'rgba(249,115,22,0.4)')}
                  onBlur={e => (e.target.style.borderColor = t.borderInput)} />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <label style={{ fontSize: 12, color: t.textDim }}>Password</label>
                  <a href="#" style={{ fontSize: 11, color: t.textMuted, textDecoration: 'none' }}
                    onMouseEnter={e => (e.currentTarget.style.color = t.textSecondary)}
                    onMouseLeave={e => (e.currentTarget.style.color = t.textMuted)}
                  >Forgot password?</a>
                </div>
                <div style={{ position: 'relative' }}>
                  <input type={showPass ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" style={{ ...inputStyle, paddingRight: 40 }}
                    onFocus={e => (e.target.style.borderColor = 'rgba(249,115,22,0.4)')}
                    onBlur={e => (e.target.style.borderColor = t.borderInput)} />
                  <button onClick={() => setShowPass(p => !p)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: t.textMuted, padding: 0, lineHeight: 1 }}>
                    {showPass ? '🙈' : '👁'}
                  </button>
                </div>
              </div>
              <button onClick={handleSubmit} disabled={loading} style={{
                width: '100%', background: loading ? 'rgba(249,115,22,0.6)' : '#f97316',
                border: 'none', borderRadius: 5, color: t.opaqueTextOnOrange, fontSize: 14, fontWeight: 700,
                padding: '11px 0', cursor: loading ? 'not-allowed' : 'pointer', marginTop: 4,
                transition: 'background 0.15s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}>
                {loading ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.8s linear infinite' }}>
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                    </svg>
                    Logging in...
                  </>
                ) : 'Log In'}
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ flex: 1, height: 1, background: t.divider }} />
                <span style={{ fontSize: 11, color: t.textMuted }}>or continue with</span>
                <div style={{ flex: 1, height: 1, background: t.divider }} />
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <SocialBtn icon="G" label="Google" />
                <SocialBtn icon="⌥" label="GitHub" />
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 12, color: t.textDim, display: 'block', marginBottom: 6 }}>Full Name</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Jane Smith" style={inputStyle}
                  onFocus={e => (e.target.style.borderColor = 'rgba(249,115,22,0.4)')}
                  onBlur={e => (e.target.style.borderColor = t.borderInput)} />
              </div>
              <div>
                <label style={{ fontSize: 12, color: t.textDim, display: 'block', marginBottom: 6 }}>Email</label>
                <input type="email" value={signupEmail} onChange={e => setSignupEmail(e.target.value)} placeholder="you@company.com" style={inputStyle}
                  onFocus={e => (e.target.style.borderColor = 'rgba(249,115,22,0.4)')}
                  onBlur={e => (e.target.style.borderColor = t.borderInput)} />
              </div>
              <div>
                <label style={{ fontSize: 12, color: t.textDim, display: 'block', marginBottom: 6 }}>Password</label>
                <div style={{ position: 'relative' }}>
                  <input type={showPass ? 'text' : 'password'} value={signupPass} onChange={e => setSignupPass(e.target.value)} placeholder="Min. 8 characters" style={{ ...inputStyle, paddingRight: 40 }}
                    onFocus={e => (e.target.style.borderColor = 'rgba(249,115,22,0.4)')}
                    onBlur={e => (e.target.style.borderColor = t.borderInput)} />
                  <button onClick={() => setShowPass(p => !p)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, color: t.textMuted, padding: 0, lineHeight: 1 }}>
                    {showPass ? '🙈' : '👁'}
                  </button>
                </div>
                {signupPass.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ height: 3, background: t.progressTrack, borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 2, width: `${passStrength * 33.33}%`, background: passColor, transition: 'width 0.3s, background 0.3s' }} />
                    </div>
                    <div style={{ fontSize: 10, color: passColor, marginTop: 4, fontFamily: 'JetBrains Mono, monospace' }}>{passLabel}</div>
                  </div>
                )}
              </div>

              <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer', fontSize: 12, color: t.textSecondary, lineHeight: 1.5 }}>
                <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} style={{ accentColor: '#f97316', marginTop: 2, flexShrink: 0 }} />
                I agree to the <a href="#" style={{ color: '#f97316', textDecoration: 'none' }}>Terms of Service</a> and <a href="#" style={{ color: '#f97316', textDecoration: 'none' }}>Privacy Policy</a>
              </label>

              <button onClick={handleSubmit} disabled={loading || !agreed} style={{
                width: '100%', background: loading ? 'rgba(249,115,22,0.6)' : (!agreed ? 'rgba(249,115,22,0.3)' : '#f97316'),
                border: 'none', borderRadius: 5, color: t.opaqueTextOnOrange, fontSize: 14, fontWeight: 700,
                padding: '11px 0', cursor: (loading || !agreed) ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}>
                {loading ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.8s linear infinite' }}>
                      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                    </svg>
                    Creating account...
                  </>
                ) : 'Create Account'}
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ flex: 1, height: 1, background: t.divider }} />
                <span style={{ fontSize: 11, color: t.textMuted }}>or continue with</span>
                <div style={{ flex: 1, height: 1, background: t.divider }} />
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <SocialBtn icon="G" label="Google" />
                <SocialBtn icon="⌥" label="GitHub" />
              </div>
            </div>
          )}
        </div>

        {/* Below-card link */}
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: t.textMuted }}>
          {tab === 'login' ? (
            <>Don&apos;t have an account?{' '}
              <button onClick={() => setTab('signup')} style={{ background: 'none', border: 'none', color: '#f97316', cursor: 'pointer', fontSize: 13, padding: 0, fontWeight: 500 }}>Sign Up</button>
            </>
          ) : (
            <>Already have an account?{' '}
              <button onClick={() => setTab('login')} style={{ background: 'none', border: 'none', color: '#f97316', cursor: 'pointer', fontSize: 13, padding: 0, fontWeight: 500 }}>Log In</button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────

const NAV: { id: Screen; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '⬛' },
  { id: 'inference', label: 'Inference', icon: '◈' },
  { id: 'benchmark', label: 'Benchmark', icon: '◉' },
  { id: 'optimization', label: 'Optimization', icon: '⚡' },
  { id: 'recommendations', label: 'AI Recommend', icon: '✦' },
  { id: 'reports', label: 'Reports', icon: '▤' },
  { id: 'history', label: 'History', icon: '◷' },
  { id: 'settings', label: 'Settings', icon: '⊙' },
]

function Sidebar({ active, setActive, onSignOut }: { active: Screen; setActive: (s: Screen) => void; onSignOut: () => void }) {
  const { t } = useTheme()
  return (
    <div style={{
      width: 220, minHeight: '100vh', background: t.sidebarBg,
      borderRight: `1px solid ${t.divider}`,
      display: 'flex', flexDirection: 'column',
      position: 'fixed', left: 0, top: 0, bottom: 0, transition: 'background 0.3s',
    }}>
      <div style={{ padding: '24px 20px 20px', borderBottom: `1px solid ${t.divider}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 7,
            background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 800, color: '#fff',
          }}>A</div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: t.text, letterSpacing: '-0.02em' }}>ArmPilot</div>
            <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace' }}>AI · v2.4.1</div>
          </div>
        </div>
      </div>

      <nav style={{ padding: '12px 10px', flex: 1 }}>
        <div style={{ fontSize: 9, color: t.textFaint, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '0.12em', padding: '8px 10px 6px', textTransform: 'uppercase' }}>Navigation</div>
        {NAV.map(({ id, label, icon }) => {
          const isActive = active === id
          return (
            <button key={id} onClick={() => setActive(id)} style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 10px', borderRadius: 6, marginBottom: 1,
              background: isActive ? t.navActive : 'transparent',
              border: 'none', cursor: 'pointer', transition: 'all 0.15s',
              color: isActive ? t.orange : t.textSecondary,
              textAlign: 'left',
            }}
              onMouseEnter={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = t.navHover }}
              onMouseLeave={e => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent' }}
            >
              <span style={{ fontSize: 14, width: 18, textAlign: 'center' }}>{icon}</span>
              <span style={{ fontSize: 13, fontWeight: isActive ? 600 : 400 }}>{label}</span>
              {isActive && <div style={{ marginLeft: 'auto', width: 3, height: 16, borderRadius: 2, background: t.orange }} />}
            </button>
          )
        })}
      </nav>

      <div style={{ padding: '12px 16px', borderTop: `1px solid ${t.divider}` }}>
        <div style={{ background: t.cardBg, borderRadius: 6, padding: '10px 12px', transition: 'background 0.3s' }}>
          <div style={{ fontSize: 10, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace', marginBottom: 6 }}>SYSTEM STATUS</div>
          <div className="flex items-center gap-2" style={{ fontSize: 12, color: t.green, marginBottom: 4 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: t.green, display: 'inline-block' }} />
            Server Online
          </div>
          <div style={{ fontSize: 11, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace' }}>CPU: 84% · Mem: 3.2GB</div>
        </div>
      </div>

      <div style={{ borderTop: `1px solid ${t.divider}`, padding: '8px 10px' }}>
        <button onClick={onSignOut} style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 10,
          padding: '9px 10px', borderRadius: 6,
          background: 'transparent', border: 'none', cursor: 'pointer',
          color: t.textMuted, textAlign: 'left', transition: 'all 0.15s',
        }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = t.navHover; (e.currentTarget as HTMLElement).style.color = t.textDim }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = t.textMuted }}
        >
          <span style={{ fontSize: 14, width: 18, textAlign: 'center' }}>⎋</span>
          <span style={{ fontSize: 13 }}>Sign Out</span>
        </button>
      </div>
    </div>
  )
}

// ─── Topbar ───────────────────────────────────────────────────────────────────

function Topbar({ screen }: { screen: Screen }) {
  const { t, isDark, setIsDark } = useTheme()
  const titles: Record<Screen, string> = {
    dashboard: 'Dashboard',
    inference: 'Model Inference',
    benchmark: 'Benchmark Runner',
    optimization: 'Optimization Engine',
    recommendations: 'AI Recommendations',
    reports: 'Performance Reports',
    history: 'Run History',
    settings: 'Settings',
  }

  return (
    <div style={{
      height: 56, background: t.sidebarBg, borderBottom: `1px solid ${t.divider}`,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 24px', position: 'fixed', top: 0, left: 220, right: 0, zIndex: 10,
      transition: 'background 0.3s',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 10, color: t.textFaint, fontFamily: 'JetBrains Mono, monospace' }}>armpilot /</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: t.text }}>{titles[screen]}</span>
      </div>
      <div className="flex items-center gap-4">
        <div style={{ fontSize: 12, color: t.textMuted, fontFamily: 'JetBrains Mono, monospace' }}>
          Arm Neoverse N1 · 64-core
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: t.green }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: t.green, display: 'inline-block', animation: 'pulse-dot 2s ease infinite' }} />
          llama.cpp v0.3.8
        </div>
        {/* ── Theme toggle ── */}
        <button
          onClick={() => setIsDark(d => !d)}
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          style={{
            background: t.ghostBg, border: `1px solid ${t.ghostBorder}`, borderRadius: 5,
            color: t.text, width: 30, height: 30, display: 'flex', alignItems: 'center',
            justifyContent: 'center', cursor: 'pointer', fontSize: 14, flexShrink: 0,
            transition: 'background 0.15s',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBgHover }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = t.ghostBg }}
        >
          {isDark ? '☀' : '☾'}
        </button>
        <div style={{
          width: 30, height: 30, borderRadius: '50%',
          background: `linear-gradient(135deg, ${t.orange}, ${t.cyan})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 700, color: '#fff', cursor: 'pointer',
        }}>A</div>
      </div>
    </div>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [flow, setFlow] = useState<AppFlow>('landing')
  const [authTab, setAuthTab] = useState<AuthTab>('signup')
  const [screen, setScreen] = useState<Screen>('dashboard')
  const [welcomeName, setWelcomeName] = useState<string | null>(null)
  const [isDark, setIsDark] = useState(true)

  const t = isDark ? darkTheme : lightTheme

  function navToAuth(tab: AuthTab) {
    setAuthTab(tab)
    setFlow('auth')
  }

  function navToDashboard(name?: string) {
    setFlow('app')
    setWelcomeName(name ?? null)
    if (name) setTimeout(() => setWelcomeName(null), 4000)
  }

  return (
    <ThemeContext.Provider value={{ t, isDark, setIsDark }}>
      <div style={{ minHeight: '100vh', background: t.bg, color: t.text, transition: 'background 0.3s, color 0.3s' }}>
        {flow === 'landing' && <LandingPage onNav={navToAuth} />}
        {flow === 'auth' && <AuthPage defaultTab={authTab} onSuccess={navToDashboard} />}
        {flow === 'app' && (() => {
          const screens: Record<Screen, React.ReactNode> = {
            dashboard: <Dashboard />,
            inference: <Inference />,
            benchmark: <Benchmark />,
            optimization: <Optimization />,
            recommendations: <Recommendations />,
            reports: <Reports />,
            history: <History />,
            settings: <Settings onSignOut={() => setFlow('landing')} />,
          }
          return (
            <>
              <Sidebar active={screen} setActive={setScreen} onSignOut={() => setFlow('landing')} />
              <Topbar screen={screen} />
              <main style={{ marginLeft: 220, paddingTop: 56 }}>
                {welcomeName && (
                  <div style={{
                    margin: '16px 28px 0', padding: '12px 16px',
                    background: `${t.green}18`, border: `1px solid ${t.green}40`,
                    borderRadius: 6, display: 'flex', alignItems: 'center', gap: 10,
                    animation: 'slide-in 0.3s ease forwards',
                  }}>
                    <span style={{ color: t.green, fontSize: 16 }}>✓</span>
                    <span style={{ fontSize: 13, color: t.text }}>
                      Welcome, <strong>{welcomeName}</strong>! Your account is ready.
                    </span>
                  </div>
                )}
                <div style={{ padding: '28px 28px', maxWidth: 1280 }}>
                  {screens[screen]}
                </div>
              </main>
            </>
          )
        })()}
      </div>
    </ThemeContext.Provider>
  )
}
