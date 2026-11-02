# FINOPS.md — Cost of a code documentation agent

## 1. System prompt tokenization

| Measure    | Value |
| ---------- | ----- |
| Tokens     | 58    |
| Characters | 295   |

**Tokenizer**: `tiktoken` 0.14.0, encoding `o200k_base` (GPT-4o). Ratio ~5.1 chars/token.

## 2. Assumptions

- System prompt: 58 tokens
- Injected code: 15,000 tokens
- Generated response: 500 tokens
- Rates: $5/M input · $15/M output

## 3. Cost of a single execution

- Input = 58 + 15,000 = **15,058 tokens** → 15,058 × 5/1M = $0.07529
- Output = 500 × 15/1M = $0.00750
- **Total = $0.08279**

## 4. Loop of 10 iterations (cumulative history)

Formula: `input_n = 15,058 + 500 × (n−1)`

| Iteration | Input  | Output | Iteration cost ($) | Cumulative ($) |
| --------- | ------ | ------ | ------------------ | -------------- |
| 1         | 15,058 | 500    | 0.08279            | 0.08279        |
| 2         | 15,558 | 500    | 0.08529            | 0.16808        |
| 3         | 16,058 | 500    | 0.08779            | 0.25587        |
| 4         | 16,558 | 500    | 0.09029            | 0.34616        |
| 5         | 17,058 | 500    | 0.09279            | 0.43895        |
| 6         | 17,558 | 500    | 0.09529            | 0.53424        |
| 7         | 18,058 | 500    | 0.09779            | 0.63203        |
| 8         | 18,558 | 500    | 0.10029            | 0.73232        |
| 9         | 19,058 | 500    | 0.10279            | 0.83511        |
| 10        | 19,558 | 500    | 0.10529            | **0.94040**    |

**Check**: Σinput = 10 × 15,058 + 500 × 45 = 173,080 → $0.86540. Σoutput = 5,000 → $0.07500. Total = **$0.94040** ✓

Extra cost vs 10 independent calls ($0.82790): **+13.6%**, due to re-sending the growing history.

## 5. Self-assessment

Both methods give $0.94040. Input grows linearly (+500 tokens/iteration), but cumulative cost grows with n² because the full history is re-sent each call.

**Optimization**: sliding window keeping only the last response → input fixed at 15,558 tokens → cumulative cost = $0.08279 + 9 × $0.08529 = **$0.85040 (−9.6%)**. Cost becomes linear in n instead of n².
