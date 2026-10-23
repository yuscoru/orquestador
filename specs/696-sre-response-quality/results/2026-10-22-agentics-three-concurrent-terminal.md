# Final read-only concurrency result — three user-launched tasks

Source: `agentics@soarplus`, ASK `696-agentics-19`, one final snapshot. Runtime PID 47862 healthy on coherent OTEL 1.38; repo commit `5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f`, dirty inventory pre-existing.

All three tasks completed with distinct task/context/eval IDs, 5 sampled cases, 10/10 case-metrics, 25/25 usage-bearing LLM calls, no tracking/LLM/case failure, persisted documents and exact task/result token agreement. All have `adk_events`, `usage_recorded=true`, no calls without usage and no provider/cost data.

| Task / target | eval_run | status / checkpoint | metric scores (hallucinations, quality) | prompt / completion / total |
|---|---|---|---|---|
| `ba216...` / websearch-agent | `10f2139e8f9948f09b8b82c21c35cbb5` | measured / true | 0.3829431438 / 0.84 | 131,782 / 76,991 / 208,773 |
| `1503...` / mcs-xsoar-radware-security-reports | `3b3b92485eb04087aa8541eadd2b3302` | judge_unavailable / false | 0.9473269615 / 0.5666666667 | 1,124,782 / 433,956 / 1,558,738 |
| `656a...` / securityalertanalysisv2 | `da7397152061483fb881a554847abafc` | judge_unavailable / false | 0.9972000689 / 1.0 | 895,530 / 363,726 / 1,259,256 |

Combined: prompt 2,152,094; completion 874,673; reasoning 456,601; cached 920,050; total 3,026,767; 75 detail entries. Task2/task3 each had one unavailable hallucinations judge score, status judge_unavailable and no checkpoint advance. Persisted pipeline summary `passed=true` is not a metric-threshold pass claim.

Overlap: task1/task2 ~59.7s; task2/task3 ~528.6s; task1/task3 none. Correlation invariant check found zero mismatches; no cross-attribution, checkpoint collision or process error. This supports request-state/accounting isolation, while not proving secret non-leakage because key values were not inspected. Earlier task1 timestamp inconsistency was resolved by the complete final log: target_finished sequence 122 at 13:48:15.648751Z, matching terminal state.

Admiral independently verified PID/listener and local Quality API behavior. Task1 eval is readable and exact. Task2/task3 endpoints return 500 because API `QualityEvaluationPoint.status` rejects writer status `judge_unavailable`; this contract finding is ISS-007, not an evaluation persistence failure.
