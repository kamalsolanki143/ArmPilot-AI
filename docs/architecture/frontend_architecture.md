# Frontend Architecture

Frontend component structure for the ArmPilot-AI dashboard.

## Overview

The frontend is a single-page React application built with Vite, Tailwind CSS v4, and Recharts. It provides a real-time dashboard for inference, benchmarking, optimization, and reporting.

## Entry Points

| File | Purpose |
|------|---------|
| `index.html` | Vite HTML shell with `#root` element |
| `src/main.tsx` | React entrypoint, mounts `App.tsx` |
| `src/App.tsx` | Main application component |
| `src/index.css` | Tailwind CSS v4 import + global styles |

## Application Structure

```
App.tsx
├── ThemeContext              # Dark/light theme provider
├── AppFlow State             # landing → auth → app
│
├── Landing Page              # Marketing / hero page
├── Auth Page                 # Login / signup forms
│
└── Dashboard Layout
    ├── Sidebar Navigation
    ├── Header (theme toggle, status indicator)
    │
    ├── Dashboard Screen      # System overview, charts, recent runs
    ├── Inference Screen      # Model selection, prompt, output, settings
    ├── Benchmark Screen      # Config form, progress, results comparison
    ├── Optimization Screen   # Quantization, threading, Arm options
    ├── Recommendations Screen# Bottleneck analysis, config comparison
    ├── Reports Screen        # Executive summary, charts, export
    ├── History Screen        # Past runs table
    └── Settings Screen       # User preferences
```

## Component Hierarchy

```
App
├── ThemeContext.Provider
│
├── [Flow: landing]
│   └── LandingPage
│
├── [Flow: auth]
│   └── AuthPage
│       ├── LoginTab
│       └── SignupTab
│
└── [Flow: app]
    └── DashboardLayout
        ├── Sidebar
        │   ├── NavItem (dashboard)
        │   ├── NavItem (inference)
        │   ├── NavItem (benchmark)
        │   ├── NavItem (optimization)
        │   ├── NavItem (recommendations)
        │   ├── NavItem (reports)
        │   └── NavItem (settings)
        │
        ├── Header
        │   ├── StatusIndicator
        │   └── ThemeToggle
        │
        └── Content Area
            ├── Dashboard
            │   ├── MetricCard (×8)
            │   ├── ChartCard (throughput, latency)
            │   └── RecentRunsTable
            │
            ├── Inference
            │   ├── ModelSelector
            │   ├── PromptEditor
            │   ├── OutputDisplay
            │   ├── GenerationSettings (sliders)
            │   ├── ModelInfo
            │   └── LiveMetrics
            │
            ├── Benchmark
            │   ├── ConfigPanel (model, concurrency, duration)
            │   ├── ProgressBar
            │   ├── MetricCards (TTFT, TPS, P95)
            │   ├── CPUChart
            │   └── ComparisonTable
            │
            ├── Optimization
            │   ├── QuantizationSelector
            │   ├── ComputeConfig (batch, threads)
            │   ├── ArmOptions (affinity, KV cache, NUMA)
            │   ├── RuntimeSelector
            │   ├── EstimatedImpact
            │   └── OptimizationProgress
            │
            ├── Recommendations
            │   ├── BottleneckAlert
            │   ├── CurrentConfig
            │   ├── RecommendedConfig
            │   ├── ReasoningCards
            │   └── ImpactMetrics
            │
            └── Reports
                ├── ExecutiveSummary
                ├── ThroughputChart
                └── DetailedMetricsTable
```

## Shared Components

| Component | Purpose |
|-----------|---------|
| `MetricCard` | Displays a single metric with value, unit, trend |
| `ChartCard` | Card wrapper for any Recharts chart |
| `Badge` | Colored status badge |
| `Btn` | Button with primary/ghost/danger/cyan variants |
| `Slider` | Range input with label and value display |
| `Toggle` | Boolean toggle switch |
| `SectionLabel` | Uppercase section header |

## Theme System

The app supports dark and light themes via React Context:

```typescript
const darkTheme = {
  bg: '#0b0e14',
  cardBg: '#141820',
  text: '#e2e8f0',
  orange: '#f97316',
  cyan: '#06b6d4',
  green: '#22c55e',
  // ...
}

const lightTheme = {
  bg: '#FAF6EF',
  cardBg: '#F0E8D8',
  text: '#1A1410',
  // ...
}
```

Usage: `const { t, isDark, setIsDark } = useTheme()`

## Charts (Recharts)

| Chart | Data | Type |
|-------|------|------|
| Throughput Over Time | tokens/sec before vs after | AreaChart |
| Latency Distribution | P50, P95, P99 latencies | LineChart |
| CPU Utilization | CPU % over time | AreaChart |
| Before vs After | Key metrics comparison | BarChart |

## Styling

- **Tailwind CSS v4** via `@tailwindcss/vite` plugin
- Utility classes directly in JSX
- Inline `style` props for theme-dependent colors
- `JetBrains Mono` for monospace/metrics, `Inter` for body text

## Build

```bash
# Development
pnpm dev        # Vite dev server on :8443

# Production
pnpm build      # Output to dist/
pnpm preview    # Preview production build
```
