# Quantization Techniques for Arm64 LLM Inference

## Overview

Quantization reduces model weight precision from FP32/FP16 to lower-bit
representations (INT8, INT4, etc.), cutting memory usage and accelerating
inference on Arm64 hardware. Arm64 processors expose fixed-width SIMD
instructions (NEON, SVE, SVE2) that make integer arithmetic particularly
efficient.

This guide covers quantization formats, calibration strategies, and
Arm64-specific implementation details.

---

## Quantization Formats

### FP16 (Half Precision)

| Property        | Value                     |
|-----------------|---------------------------|
| Bits per weight | 16                        |
| Memory reduction | 2x vs FP32               |
| Quality loss    | Negligible for most models |
| Arm64 support   | Native via NEON FP16      |

FP16 is the baseline for Arm64 inference. Every modern Arm core supports
half-precision floating point through the `FPCR` register and NEON
`FMUL`/`FADD` instructions. No special calibration is required.

```c
// FP16 dot product using Arm NEON
float16x8_t va = vld1q_f16(ptr_a);
float16x8_t vb = vld1q_f16(ptr_b);
float32x4_t acc = vmlal_high_f32(vmlal_f32(vdupq_n_f32(0), vget_low_f16(va), vget_low_f16(vb)),
                                  vget_high_f16(va), vget_high_f16(vb));
```

### BF16 (Brain Float 16)

| Property        | Value                           |
|-----------------|---------------------------------|
| Bits per weight | 16                              |
| Memory reduction | 2x vs FP32                     |
| Quality loss    | Comparable to FP16              |
| Arm64 support   | SVE2 (Arm v9.0+)               |

BF16 trades dynamic range for simpler rounding. Arm v9 cores with SVE2
support BF16 natively via `BFDOT` and `BFMMLA` instructions. On older
cores without SVE2, BF16 must be emulated, making FP16 the better choice.

```c
// BF16 matrix multiply using Arm SVE2
svbfloat16_t va = svld1_bf16(svptrue_b16(), ptr_a);
svbfloat16_t vb = svld1_bf16(svptrue_b16(), ptr_b);
svfloat32_t acc = svbfmmla_f32(svdupq_n_f32(0), va, vb);
```

### INT8 Quantization

| Property        | Value                           |
|-----------------|---------------------------------|
| Bits per weight | 8                               |
| Memory reduction | 4x vs FP32                     |
| Quality loss    | 0.5-2% perplexity increase     |
| Arm64 support   | Native via NEON SQRDMULH       |

INT8 is the most practical quantization format for production Arm64
deployments. Arm NEON provides saturating arithmetic instructions
(`SQDMULH`, `SQRDMLAH`) that accelerate INT8 matrix multiplication
without overflow.

**Symmetric vs Asymmetric:**

- **Symmetric**: Zero-point = 0, simpler hardware path. Use when weight
  distributions are roughly centered.
- **Asymmetric**: Non-zero zero-point, better utilization of the INT8
  range. Use when distributions are skewed.

```c
// INT8 symmetric quantized matmul (per-channel)
int8x16_t va = vld1q_s8(ptr_a);
int8x16_t vb = vld1q_s8(ptr_b);
int32x4_t acc = vdotq_s32(vdupq_n_s32(0), va, vb);
// Dequantize: result = acc * (scale_a * scale_b)
```

### INT4 Quantization

| Property        | Value                           |
|-----------------|---------------------------------|
| Bits per weight | 4                               |
| Memory reduction | 8x vs FP32                     |
| Quality loss    | 2-5% perplexity increase       |
| Arm64 support   | Requires unpacking to INT8      |

INT4 provides the highest memory reduction but requires careful
implementation on Arm64. There are no native INT4 arithmetic instructions,
so weights must be unpacked to INT8 before computation.

**GPTQ vs GGML INT4:**

- **GPTQ**: Group-wise quantization with calibration. Better quality,
  requires group scales stored alongside weights.
- **GGML/GGUF Q4_0/Q4_1**: Simpler block quantization. Faster
  decompression, lower quality than GPTQ.

```c
// INT4 unpacking on Arm64 (low nibble extraction)
uint8x16_t packed = vld1q_u8(ptr_packed);
uint8x16_t low = vandq_u8(packed, vdupq_n_u8(0x0F));
uint8x16_t high = vshrq_n_u8(packed, 4);
// Reinterpret as signed and shift to [-8, 7]
int8x16_t low_s = vsubq_s8(vreinterpretq_s8_u8(low), vdupq_n_s8(8));
int8x16_t high_s = vsubq_s8(vreinterpretq_s8_u8(high), vdupq_n_s8(8));
```

### Mixed-Precision Quantization

Not all layers tolerate quantization equally. Mixed-precision strategies
assign different bit-widths to different layers:

1. **Sensitivity analysis**: Measure perplexity degradation per layer
   when quantized in isolation.
2. **Guard bands**: Keep attention projection layers and output heads at
   higher precision (FP16 or INT8) while quantizing FFN layers to INT4.
3. **Head/hidden dimension alignment**: Avoid quantizing layers whose
   dimensions are not multiples of 8 (NEON width) or 16 (SVE length).

A typical mixed-precision assignment for a 7B parameter model:

| Component         | Precision | Rationale                        |
|-------------------|-----------|----------------------------------|
| Embedding         | FP16      | High sensitivity to precision    |
| Attention QKV     | INT8      | Moderate sensitivity              |
| Attention output  | INT8      | Moderate sensitivity              |
| FFN up/gate       | INT4      | Low sensitivity, large tensors    |
| FFN down          | INT4      | Low sensitivity, large tensors    |
| LM head           | FP16      | Final projection, high impact    |

---

## Quantization Methods

### Post-Training Quantization (PTQ)

Apply quantization after training without retraining. Requires a small
calibration dataset (100-1000 samples).

```python
# llama.cpp-style PTQ calibration
import numpy as np

def calibration_loop(model, calibration_data, n_bits=8):
    """Collect activation statistics for quantization thresholds."""
    scales = {}
    for layer in model.layers:
        activations = layer.forward(calibration_data)
        # Symmetric range: max absolute value
        abs_max = np.max(np.abs(activations), axis=0)
        scale = abs_max / (2**(n_bits-1) - 1)
        scales[layer.name] = scale
    return scales
```

### Quantization-Aware Training (QAT)

Inject fake quantization nodes during training so the model learns to
compensate for precision loss. 2-5x more expensive than PTQ but produces
better results at INT4.

### SmoothQuant

Migrate quantization difficulty from activations to weights. Activations
have outlier channels that are hard to quantize; SmoothQuant applies a
per-channel scale to smooth the activation distribution.

```
Y = (Xdiag(s)^{-1}) * (diag(s)W) = X' * W'
```

Where `s` is chosen to balance the quantization difficulty between `X`
and `W`.

---

## Arm64-Specific Considerations

### NEON Instruction Selection

Arm NEON operates on 128-bit vectors. For INT8, this means 16 elements
per instruction cycle:

```c
// Batch INT8 dot product (16 elements per cycle)
int8x16_t a = vld1q_s8(ptr_a + i);
int8x16_t b = vld1q_s8(ptr_b + i);
acc = vdotq_s32(acc, a, b);  // Signed dot product
```

### SVE/SVE2 Advantages (Arm v9.0+)

Scalable Vector Extension vectors are variable-length (128-2048 bits),
allowing the same code to exploit wider hardware:

```c
// SVE2 INT8 matmul — width agnostic
svint8_t va = svld1_s8(svptrue_b8(), ptr_a);
svint8_t vb = svld1_s8(svptrue_b8(), ptr_b);
svint32_t acc = svdot_s32(svdupq_n_s32(0), va, vb);
```

SVE also provides gather loads (`svld1_gather`) useful for sparse
quantized weight access.

### Cache Line and Alignment

Arm64 cache lines are typically 64 bytes. Quantized weight tensors
should be aligned to 64-byte boundaries to avoid cache line splits:

```c
// Aligned allocation for quantized weights
void* ptr;
posix_memalign(&ptr, 64, tensor_size);
```

### Memory Bandwidth Bottleneck

Quantization's primary benefit on Arm64 is reducing memory bandwidth
pressure, not arithmetic throughput. A 7B FP16 model requires ~14 GB
of weight data; INT4 reduces this to ~3.5 GB. On devices with limited
memory bandwidth (e.g., 25-50 GB/s), this directly translates to
faster time-to-first-token.

---

## Performance Trade-offs

| Format | Memory (7B model) | TTFT (est.) | Perplexity Delta | Hardware Required |
|--------|-------------------|-------------|------------------|-------------------|
| FP32   | 28 GB             | ~1.2s       | Baseline         | Any               |
| FP16   | 14 GB             | ~0.6s       | +0.00            | Arm v8.2+         |
| BF16   | 14 GB             | ~0.6s       | +0.01            | Arm v9.0+         |
| INT8   | 7 GB              | ~0.3s       | +0.5-2%          | Arm v8.2+         |
| INT4   | 3.5 GB            | ~0.15s      | +2-5%            | Any (unpack)      |

**Key insight**: TTFT (time-to-first-token) is almost entirely
bandwidth-bound during prefill. INT4 provides the largest TTFT
improvement because it minimizes data movement.

---

## Best Practices

1. **Always benchmark on target hardware.** Quantization quality varies
   by model architecture and calibration data.
2. **Use INT4 for memory-constrained devices** (phones, edge) and INT8
   for server-grade Arm64 (Graviton, Ampere).
3. **Preserve FP16 for attention logits** to avoid softmax instability.
4. **Store group scales alongside INT4 weights** (GPTQ format) for
   better quality than naive per-tensor quantization.
5. **Validate with downstream tasks**, not just perplexity. A 2%
   perplexity increase may translate to a 10% drop on reasoning benchmarks.
6. **Profile memory bandwidth** before and after quantization — the
   bottleneck shifts from compute to bandwidth as you go lower precision.
7. **Consider SVE2 BF16** on Arm v9 cores as a zero-loss alternative
   to INT8 for supported hardware.
