# Arm Performix Integration

How ArmPilot-AI integrates with Arm Performix for hardware-level performance analysis on Arm Neoverse platforms.

## Overview

[Arm Performix](https://developer.arm.com/servers-and-cloud-computing/arm-performix) is a free performance analysis toolkit for developers building on Arm-based infrastructure. It combines target-side data collection with guided analysis, function-level insights, and desktop visualizations.

ArmPilot-AI uses Performix to correlate application-level LLM inference metrics (TTFT, TPS, latency) with hardware-level execution data (CPU microarchitecture bottlenecks, SIMD utilization, memory bandwidth).

## Architecture Integration

```
┌──────────────────────────────────────────────────────┐
│                  ArmPilot-AI Pipeline                  │
│                                                        │
│  ┌────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │ Benchmark  │───▶│   Metric     │───▶│  Report   │ │
│  │ Driver     │    │  Collector   │    │  Builder  │ │
│  └────────────┘    └──────────────┘    └───────────┘ │
│        │                                       │       │
│        │         ┌──────────────┐              │       │
│        └────────▶│ Arm Performix│◀─────────────┘       │
│                  │  apx CLI     │                      │
│                  └──────┬───────┘                      │
│                         │                              │
│                  ┌──────▼───────┐                      │
│                  │  Target      │                      │
│                  │  Machine     │                      │
│                  │  (Arm64)     │                      │
│                  └──────────────┘                      │
└──────────────────────────────────────────────────────┘
```

## Installing Arm Performix

### CLI Installation

```bash
# Download Arm Performix CLI for your platform
# Linux Arm64
curl -LO https://artifacts.tools.arm.com/arm-performix/cli/latest/ArmPerformix-cli-linux-arm64.tar.gz
tar xzf ArmPerformix-cli-linux-arm64.tar.gz
sudo mv apx /usr/local/bin/

# Verify installation
apx --version
```

### Building from Source

```bash
# Prerequisites: C/C++ compiler, curl, unzip
sudo apt install build-essential curl unzip

# Clone and bootstrap
git clone https://github.com/arm/performix.git
cd performix
./bootstrap

# Build the CLI
mise exec -- task install

# Binary available at
ls core/apap-cli/apx
```

## Recipe Configuration

Performix uses recipes to define what performance data to collect and how to analyze it. ArmPilot-AI configures recipes optimized for LLM inference profiling.

### System Utilization Recipe

Monitor CPU, memory, and I/O during inference:

```yaml
# configs/performix_system_utilization.yaml
recipe: system_utilization
target: localhost
timeout: 30
deploy_tools: true
system_wide: true

collection:
  cpu_utilization: true
  memory_bandwidth: true
  io_wait: true
  context_switches: true

output:
  format: json
  directory: logs/performix
```

### Code Hotspots Recipe

Identify where CPU time is spent in inference code:

```yaml
# configs/performix_hotspots.yaml
recipe: code_hotspots
target: localhost
timeout: 60
deploy_tools: true

collection:
  flame_graph: true
  call_stacks: true
  source_attribution: true

analysis:
  top_functions: 20
  min_sample_percentage: 0.5
```

### CPU Microarchitecture Recipe

Analyze CPU pipeline bottlenecks using Topdown methodology:

```yaml
# configs/performix_microarch.yaml
recipe: cpu_microarchitecture
target: localhost
timeout: 60
deploy_tools: true

collection:
  topdown_analysis: true
  frontend_bound: true
  backend_bound: true
  bad_speculation: true
  retiring: true
```

### Instruction Mix Recipe

Understand how code uses Arm architectural features:

```yaml
# configs/performix_instruction_mix.yaml
recipe: instruction_mix
target: localhost
timeout: 60
deploy_tools: true

collection:
  scalar_vs_simd: true
  neon_usage: true
  sve_usage: true
  sve2_usage: true
  crypto_extensions: true
```

## Integration with Benchmark Pipeline

### Automated Profiling

```python
import subprocess
import json
from pathlib import Path

class PerformixIntegrator:
    """Integrates Arm Performix into the ArmPilot-AI benchmark pipeline."""
    
    def __init__(self, apx_binary: str = "apx", target: str = "localhost"):
        self.apx = apx_binary
        self.target = target
        self.output_dir = Path("logs/performix")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_recipe(
        self,
        recipe: str,
        timeout: int = 60,
        system_wide: bool = True,
        extra_args: list[str] = None,
    ) -> dict:
        """Execute a Performix recipe and return parsed results."""
        cmd = [
            self.apx, "recipe", "run", recipe,
            "--target", self.target,
            "--timeout", str(timeout),
            "--deploy-tools",
        ]
        
        if system_wide:
            cmd.append("--system-wide")
        
        if extra_args:
            cmd.extend(extra_args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 30,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Performix recipe failed: {result.stderr}")
        
        return self._parse_output(result.stdout)
    
    def _parse_output(self, raw_output: str) -> dict:
        """Parse Performix JSON output."""
        # Find JSON in output (may have log lines before it)
        json_start = raw_output.find("{")
        json_end = raw_output.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            return {"raw_output": raw_output}
        
        return json.loads(raw_output[json_start:json_end])
```

### Benchmark-Profiling Correlation

Run benchmarks and profiling in parallel to correlate application metrics with hardware behavior:

```python
import threading

def run_benchmark_with_profiling(
    benchmark_fn,
    performix: PerformixIntegrator,
    recipes: list[str] = ["system_utilization", "code_hotspots"],
) -> dict:
    """Run benchmark with concurrent Performix profiling."""
    
    # Start profiling in background threads
    profiling_results = {}
    profiling_threads = []
    
    def run_recipe(recipe_name):
        profiling_results[recipe_name] = performix.run_recipe(recipe_name)
    
    for recipe in recipes:
        thread = threading.Thread(target=run_recipe, args=(recipe,))
        thread.start()
        profiling_threads.append(thread)
    
    # Run the benchmark
    benchmark_results = benchmark_fn()
    
    # Wait for profiling to complete
    for thread in profiling_threads:
        thread.join(timeout=120)
    
    # Correlate results
    return {
        "benchmark": benchmark_results,
        "profiling": profiling_results,
        "correlation": correlate_results(benchmark_results, profiling_results),
    }

def correlate_results(benchmark: dict, profiling: dict) -> dict:
    """Correlate application-level metrics with hardware profiling data."""
    correlation = {}
    
    if "system_utilization" in profiling:
        sys_util = profiling["system_utilization"]
        correlation["cpu_bottleneck"] = analyze_cpu_bottleneck(
            benchmark["throughput"]["output_tps"],
            sys_util.get("cpu_utilization", {}),
        )
    
    if "code_hotspots" in profiling:
        hotspots = profiling["code_hotspots"]
        correlation["hot_function"] = hotspots.get("top_functions", [{}])[0]
        correlation["optimization_target"] = identify_optimization_target(
            hotspots,
            benchmark,
        )
    
    return correlation

def analyze_cpu_bottleneck(tps: float, cpu_util: dict) -> str:
    """Determine if CPU is the throughput bottleneck."""
    core_util = cpu_util.get("core_utilization_pct", 0)
    mem_bw_util = cpu_util.get("memory_bandwidth_utilization_pct", 0)
    
    if core_util > 85 and mem_bw_util < 50:
        return "compute_bound"
    elif mem_bw_util > 80:
        return "memory_bound"
    elif core_util < 50:
        return "underutilized"
    return "balanced"

def identify_optimization_target(hotspots: dict, benchmark: dict) -> dict:
    """Identify the primary optimization target from profiling data."""
    top_functions = hotspots.get("top_functions", [])
    
    for func in top_functions:
        if func.get("sample_percentage", 0) > 30:
            return {
                "function": func["name"],
                "line": func.get("source_line"),
                "bottleneck": func.get("bottleneck_type", "unknown"),
                "suggestion": func.get("optimization_suggestion", ""),
            }
    
    return {"function": "none_dominant", "bottleneck": "distributed"}
```

## CI/CD Integration

### Performance Regression Detection

```yaml
# .github/workflows/performance-regression.yml
name: Performance Regression Check
on:
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Arm64 environment
        uses: uraimo/run-on-arch-action@v2
        with:
          arch: aarch64
          distro: ubuntu22.04
          
      - name: Install Arm Performix
        run: |
          curl -LO https://artifacts.tools.arm.com/arm-performix/cli/latest/ArmPerformix-cli-linux-arm64.tar.gz
          tar xzf ArmPerformix-cli-linux-arm64.tar.gz
          sudo mv apx /usr/local/bin/
          
      - name: Run benchmark with profiling
        run: |
          python benchmark.py \
            --model llama-3-8b \
            --quant Q4_K_M \
            --output results.json \
            --performix --performix-recipes system_utilization,code_hotspots
            
      - name: Check for regressions
        run: |
          python scripts/check_regression.py \
            --baseline main \
            --current results.json \
            --threshold 5.0
```

### Automated Optimization Validation

```python
def validate_optimization(
    before_results: dict,
    after_results: dict,
    performix_before: dict,
    performix_after: dict,
) -> dict:
    """Validate that an optimization improved performance."""
    
    tps_change = (
        (after_results["throughput"]["output_tps"] - 
         before_results["throughput"]["output_tps"]) /
        before_results["throughput"]["output_tps"] * 100
    )
    
    ttft_change = (
        (after_results["latency"]["ttft_ms"] - 
         before_results["latency"]["ttft_ms"]) /
        before_results["latency"]["ttft_ms"] * 100
    )
    
    simd_change = None
    if "instruction_mix" in performix_before and "instruction_mix" in performix_after:
        before_simd = performix_before["instruction_mix"].get("simd_percentage", 0)
        after_simd = performix_after["instruction_mix"].get("simd_percentage", 0)
        simd_change = after_simd - before_simd
    
    return {
        "tps_change_pct": tps_change,
        "ttft_change_pct": ttft_change,
        "simd_usage_change_pct": simd_change,
        "improvement": tps_change > 0 and ttft_change < 0,
        "recommendation": generate_recommendation(tps_change, ttft_change, simd_change),
    }

def generate_recommendation(tps_change, ttft_change, simd_change) -> str:
    if tps_change > 20:
        return "Significant throughput improvement. Consider merging."
    elif tps_change > 5:
        return "Moderate improvement. Verify statistical significance."
    elif tps_change < -5:
        return "Performance regression detected. Investigate root cause."
    
    if simd_change and simd_change > 20:
        return "SIMD utilization improved significantly."
    
    return "No significant change detected."
```

## MCP Server Integration

Arm Performix integrates with the Arm MCP Server for AI-assisted analysis:

```python
class PerformixMCPClient:
    """Query Performix data via Arm MCP Server for AI-assisted optimization."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080"):
        self.server_url = mcp_server_url
    
    def query_hotspots(self, run_id: str) -> dict:
        """Query hotspot analysis from the MCP server."""
        response = httpx.post(
            f"{self.server_url}/mcp/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "performix_query_hotspots",
                    "arguments": {"run_id": run_id, "top_n": 10},
                },
            },
        )
        return response.json()
    
    def query_topdown(self, run_id: str) -> dict:
        """Query Topdown analysis results."""
        response = httpx.post(
            f"{self.server_url}/mcp/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "performix_query_topdown",
                    "arguments": {"run_id": run_id},
                },
            },
        )
        return response.json()
    
    def query_instruction_mix(self, run_id: str) -> dict:
        """Query instruction mix analysis."""
        response = httpx.post(
            f"{self.server_url}/mcp/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": "performix_query_instruction_mix",
                    "arguments": {"run_id": run_id},
                },
            },
        )
        return response.json()
```

## Reference Recipes for LLM Inference

| Recipe | Use Case | Key Metrics |
|--------|----------|-------------|
| `system_utilization` | Baseline system profiling | CPU%, Mem BW, I/O wait |
| `code_hotspots` | Find inference hot functions | Function time%, call stacks |
| `cpu_microarchitecture` | Identify pipeline bottlenecks | Frontend/Backend bound, retiring% |
| `instruction_mix` | SIMD/vectorization opportunities | NEON/SVE/SVE2 usage% |
| `memory_access` | Memory latency patterns | Cache hit rates, TLB misses |

## References

- [Arm Performix Documentation](https://developer.arm.com/servers-and-cloud-computing/arm-performix)
- [Arm Performix GitHub](https://github.com/arm/performix)
- [Arm Topdown Methodology](https://developer.arm.com/documentation/109542/0100/)
- [Arm MCP Server](https://developer.arm.com/servers-and-cloud-computing/arm-mcp-server)
- [Arm Learning Paths - LLM](https://learn.arm.com/tag/llm)
