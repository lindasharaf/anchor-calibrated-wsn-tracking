## Table I - coverage % (mean ± std over runs) / mean radius m.  Target 90%.

S1 = whole run; S2-S4 = second half (after the change).

| Method | Normal room | Walls appear | Signals worsen | Anchor breaks |
|---|---|---|---|---|
| Kalman ellipse | 84.5 ± 3.4 / 3.4 | 4.4 ± 0.6 / 3.4 | 6.0 ± 1.4 / 3.4 | 88.0 ± 3.8 / 3.4 |
| One-time survey | 89.0 ± 3.3 / 5.7 | 9.4 ± 1.4 / 5.7 | 10.7 ± 1.8 / 5.7 | 89.6 ± 3.5 / 5.7 |
| Oracle, 10% feedback | 90.4 ± 4.0 / 6.6 | 85.3 ± 6.3 / 19.8 | 86.4 ± 5.1 / 19.6 | 91.1 ± 4.4 / 6.8 |
| Oracle (true feedback) | 89.9 ± 0.2 / 5.9 | 91.1 ± 0.6 / 20.1 | 95.3 ± 1.0 / 20.5 | 89.5 ± 0.6 / 5.9 |
| Ours | 93.7 ± 0.8 / 6.6 | 97.5 ± 0.7 / 25.4 | 97.0 ± 1.0 / 25.6 | 94.3 ± 1.3 / 6.8 |

## Table II - variants of our method (coverage % / radius m), 50 runs

| Variant | Normal room | Walls appear | Signals worsen | Anchor breaks |
|---|---|---|---|---|
| Ours-U (plain) | 97.0 / 7.4 | 98.8 / 24.8 | 99.1 / 23.9 | 97.9 / 7.9 |
| Ours | 93.7 / 6.6 | 97.5 / 25.4 | 97.0 / 25.6 | 94.3 / 6.8 |
| Ours-G (geometry) | 91.5 / 6.2 | 60.4 / 16.6 | 76.0 / 18.5 | 93.4 / 6.5 |
| Ours-U + ACI | 96.8 / 7.3 | 99.0 / 24.8 | 99.1 / 23.9 | 97.6 / 7.8 |
| Ours + ACI | 93.4 / 6.5 | 97.4 / 25.3 | 96.3 / 25.2 | 93.8 / 6.7 |

## Table III - anchor density (coverage % / radius m)

| Anchors | Method | Normal room | Walls appear |
|---|---|---|---|
| 9 | One-time survey | 90.5 / 8.5 | 40.0 / 8.5 |
| 9 | Oracle (true feedback) | 90.1 / 8.6 | 91.5 / 16.8 |
| 9 | Ours | 95.4 / 11.0 | 71.3 / 13.4 |
| 16 | One-time survey | 89.0 / 5.7 | 9.4 / 5.7 |
| 16 | Oracle (true feedback) | 89.9 / 5.9 | 91.1 / 20.1 |
| 16 | Ours | 93.7 / 6.6 | 97.5 / 25.4 |
| 25 | One-time survey | 86.9 / 4.5 | 6.7 / 4.5 |
| 25 | Oracle (true feedback) | 89.7 / 4.8 | 90.9 / 14.2 |
| 25 | Ours | 92.3 / 5.1 | 94.0 / 16.2 |

## Recovery after the change (steps until 30-step rolling coverage >= 88%)

- **Walls appear**: Kalman ellipse: never (0/50); One-time survey: never (0/50); Oracle, 10% feedback: median 31 (50/50 recover); Oracle (true feedback): median 7 (50/50 recover); Ours: median 0 (50/50 recover)
- **Signals worsen**: Kalman ellipse: never (0/50); One-time survey: never (0/50); Oracle, 10% feedback: median 46 (50/50 recover); Oracle (true feedback): median 0 (50/50 recover); Ours: median 0 (50/50 recover)

## Broken-anchor detection
- detected in 50/50 runs; delay median 4 steps, max 4
- false alarms (any anchor flagged without a fault): 0 of 200 runs; wrong anchor flagged in S4: 0

Runs per configuration: 50