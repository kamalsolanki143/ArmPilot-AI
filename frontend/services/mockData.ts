export interface MetricCardData {
  title: string;
  value: string;
  unit?: string;
  change: string;
  changeType: "positive" | "negative" | "neutral";
  color: "cyan" | "green" | "orange" | "purple" | "neutral";
  subtext: string;
}

export interface RunRecord {
  id: string;
  model: string;
  config: string;
  ttft: string;
  tps: number;
  p95: string;
  status: "PASS" | "FAIL" | "RUNNING";
  date: string;
  memory: string;
  cpu: string;
}

export interface ModelItem {
  id: string;
  name: string;
  parameters: string;
  quantization: string;
  size: string;
  provider: string;
  runtime: string;
  backend: string;
  description: string;
  contextWindow: number;
  recommendedThreads: number;
}

export const INITIAL_METRICS: MetricCardData[] = [
  {
    title: "TTFT",
    value: "48",
    unit: "ms",
    change: "-62% vs baseline",
    changeType: "positive",
    color: "cyan",
    subtext: "Time to first token",
  },
  {
    title: "TOKENS / SEC",
    value: "34.7",
    unit: "tps",
    change: "+169% vs baseline",
    changeType: "positive",
    color: "green",
    subtext: "Generation velocity",
  },
  {
    title: "P95 LATENCY",
    value: "104",
    unit: "ms",
    change: "-66% vs baseline",
    changeType: "positive",
    color: "orange",
    subtext: "95th percentile latency",
  },
  {
    title: "THROUGHPUT",
    value: "2,840",
    unit: "tok/min",
    change: "+2.7× vs baseline",
    changeType: "positive",
    color: "purple",
    subtext: "Aggregate rate",
  },
  {
    title: "CPU UTILIZATION",
    value: "84%",
    unit: "",
    change: "64 cores active",
    changeType: "neutral",
    color: "neutral",
    subtext: "Neoverse N1 cluster",
  },
  {
    title: "MEMORY USAGE",
    value: "3.2 GB",
    unit: "",
    change: "Model: Llama-3.2-3B INT4",
    changeType: "neutral",
    color: "neutral",
    subtext: "Working set footprint",
  },
  {
    title: "MODEL SIZE",
    value: "2.1 GB",
    unit: "",
    change: "INT4 quantized",
    changeType: "neutral",
    color: "neutral",
    subtext: "GGUF Q4_K_M",
  },
  {
    title: "ACTIVE SESSIONS",
    value: "12",
    unit: "",
    change: "max concurrency: 16",
    changeType: "neutral",
    color: "neutral",
    subtext: "Inference queue",
  },
];

export const MOCK_RUNS: RunRecord[] = [
  {
    id: "RUN-0042",
    model: "Llama-3.2-3B",
    config: "INT4 + batch=8",
    ttft: "48ms",
    tps: 34.7,
    p95: "104ms",
    status: "PASS",
    date: "2026-08-14 22:15 UTC",
    memory: "3.2 GB",
    cpu: "84%",
  },
  {
    id: "RUN-0041",
    model: "Llama-3.2-3B",
    config: "FP16 baseline",
    ttft: "127ms",
    tps: 12.9,
    p95: "310ms",
    status: "PASS",
    date: "2026-08-14 21:40 UTC",
    memory: "6.4 GB",
    cpu: "91%",
  },
  {
    id: "RUN-0040",
    model: "Mistral-7B",
    config: "INT8 + batch=4",
    ttft: "91ms",
    tps: 18.2,
    p95: "198ms",
    status: "PASS",
    date: "2026-08-14 20:05 UTC",
    memory: "7.3 GB",
    cpu: "88%",
  },
  {
    id: "RUN-0039",
    model: "Phi-3-mini",
    config: "INT4 + threads=16",
    ttft: "31ms",
    tps: 51.3,
    p95: "78ms",
    status: "PASS",
    date: "2026-08-14 18:32 UTC",
    memory: "2.4 GB",
    cpu: "76%",
  },
  {
    id: "RUN-0038",
    model: "Mistral-7B",
    config: "FP32 baseline",
    ttft: "204ms",
    tps: 7.1,
    p95: "489ms",
    status: "FAIL",
    date: "2026-08-14 16:10 UTC",
    memory: "14.8 GB",
    cpu: "98%",
  },
  {
    id: "RUN-0037",
    model: "Gemma-2B",
    config: "INT8 + batch=8",
    ttft: "38ms",
    tps: 44.1,
    p95: "92ms",
    status: "PASS",
    date: "2026-08-14 14:20 UTC",
    memory: "2.9 GB",
    cpu: "68%",
  },
  {
    id: "RUN-0036",
    model: "Qwen2.5-7B",
    config: "INT4 + batch=4",
    ttft: "82ms",
    tps: 22.4,
    p95: "175ms",
    status: "PASS",
    date: "2026-08-14 12:45 UTC",
    memory: "4.8 GB",
    cpu: "82%",
  },
  {
    id: "RUN-0035",
    model: "Llama-3.2-3B",
    config: "FP32 baseline",
    ttft: "185ms",
    tps: 8.3,
    p95: "420ms",
    status: "PASS",
    date: "2026-08-14 10:15 UTC",
    memory: "6.8 GB",
    cpu: "94%",
  },
];

export const MOCK_MODELS: ModelItem[] = [
  {
    id: "llama-3.2-3b",
    name: "Llama 3.2 3B",
    parameters: "3.2B",
    quantization: "INT4",
    size: "2.1 GB",
    provider: "Meta AI",
    runtime: "llama.cpp",
    backend: "Arm NEON + SVE2",
    description: "Ultra-compact instruction model optimized for edge and high-throughput Arm server inference.",
    contextWindow: 128000,
    recommendedThreads: 32,
  },
  {
    id: "mistral-7b",
    name: "Mistral 7B Instruct",
    parameters: "7.2B",
    quantization: "INT8",
    size: "7.3 GB",
    provider: "Mistral AI",
    runtime: "llama.cpp",
    backend: "Arm NEON + SVE2",
    description: "Industry-standard general purpose reasoning model with sliding window attention.",
    contextWindow: 32768,
    recommendedThreads: 32,
  },
  {
    id: "phi-3-mini",
    name: "Phi-3 Mini",
    parameters: "3.8B",
    quantization: "INT4",
    size: "2.4 GB",
    provider: "Microsoft",
    runtime: "llama.cpp",
    backend: "Arm NEON + SVE2",
    description: "Highly capable small language model with state-of-the-art math and coding capabilities.",
    contextWindow: 128000,
    recommendedThreads: 16,
  },
  {
    id: "gemma-2b",
    name: "Gemma 2B",
    parameters: "2.0B",
    quantization: "INT8",
    size: "2.9 GB",
    provider: "Google DeepMind",
    runtime: "llama.cpp",
    backend: "Arm NEON + SVE2",
    description: "Lightweight and efficient model built from the same research and technology used to create Gemini.",
    contextWindow: 8192,
    recommendedThreads: 16,
  },
  {
    id: "qwen2.5-7b",
    name: "Qwen2.5 7B",
    parameters: "7.6B",
    quantization: "INT4",
    size: "4.8 GB",
    provider: "Alibaba Cloud",
    runtime: "llama.cpp",
    backend: "Arm NEON + SVE2",
    description: "Exceptional multilingual and code intelligence model with dense GGUF Arm vector acceleration.",
    contextWindow: 32768,
    recommendedThreads: 32,
  },
];

export const MOCK_HARDWARE_SPECS = {
  cpu: "Arm Neoverse N1 · 64-core",
  memory: "128 GB DDR4-3200 ECC",
  os: "Ubuntu 24.04 LTS (aarch64)",
  kernel: "Linux 6.8.0-arm64-generic",
  armPilotVersion: "v2.4.1",
  llamaCppVersion: "v0.3.8 (b3490)",
  ggufVersion: "v3",
  instructionSets: ["NEON", "SVE2", "DotProd", "FP16-Vector", "AES"],
  l1Cache: "64 KB per core",
  l2Cache: "1 MB per core",
  l3Cache: "64 MB System Level Cache",
};

export const MOCK_REPORT_METRICS = [
  { metric: "TTFT (Time to First Token)", baseline: "127 ms", optimized: "48 ms", delta: "-62%", status: "IMPROVED" },
  { metric: "Tokens / Second", baseline: "12.9", optimized: "34.7", delta: "+169%", status: "IMPROVED" },
  { metric: "P50 Latency", baseline: "82 ms", optimized: "62 ms", delta: "-24%", status: "IMPROVED" },
  { metric: "P95 Latency", baseline: "310 ms", optimized: "104 ms", delta: "-66%", status: "IMPROVED" },
  { metric: "P99 Latency", baseline: "481 ms", optimized: "162 ms", delta: "-66%", status: "IMPROVED" },
  { metric: "Memory Usage", baseline: "6.4 GB", optimized: "3.2 GB", delta: "-50%", status: "IMPROVED" },
  { metric: "CPU Utilization", baseline: "91%", optimized: "84%", delta: "-7pp", status: "IMPROVED" },
  { metric: "Model Size", baseline: "6.4 GB", optimized: "2.1 GB", delta: "-67%", status: "IMPROVED" },
];
