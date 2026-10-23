# Read-only concurrency snapshot — three user-launched tasks

Source: `agentics@soarplus`, ASK `696-agentics-18`, exactly one snapshot. Runtime PID 47862 healthy on coherent OTEL 1.38; repo commit `5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f`, pre-existing dirty tree.

## ba216693-6cba-4d8e-b579-0665b1f926af

Terminal completed. Target `websearch-agent`, eval_run `10f2139e8f9948f09b8b82c21c35cbb5`, 44 candidates/sample 5, 10/10 cases, 25/25 usage-bearing LLM calls, no failures. Persisted/checkpoint committed, `adk_events`, usage_recorded true and exact task/result agreement: prompt 131,782; completion 76,991; reasoning 48,695; cached 0; total 208,773. Scores: hallucinations 0.382943143812709; response quality 0.8400000000000001. The worker report associates sequence 122 target_finished with an earlier timestamp inconsistent with the reported log span/terminal timestamp; only sequence/terminal state is relied upon pending any later final correlation.

## 1503c2f4-c7d8-4a81-876e-53f05d5a7121

Working at snapshot. Target `mcs-xsoar-radware-security-reports`, eval_run `3b3b92485eb04087aa8541eadd2b3302`, candidates/sample 5/5. Latest `llm_started` sequence 39; cases 5 started/1 finished; LLM 8 started/4 usage-finished. Partial task usage: prompt 38,211; completion 83,471; reasoning 50,142; cached 0; total 121,682. No persisted result/checkpoint/accounting path or usage_recorded yet; no terminal inference.

## 656a08b5-d125-4d66-86db-a03dda8607a1

Working at snapshot. Target `securityalertanalysisv2`, eval_run `da7397152061483fb881a554847abafc`, candidates 28/sample 5. Latest heartbeat sequence 24; cases 5 started/0 finished; LLM 5 started/0 usage-finished. No task usage or persisted result/checkpoint/accounting path yet; no terminal inference.

## Concurrency observation

Task1/task2 overlapped about 60.6s and task2/task3 about 59.0s; task1/task3 did not overlap. All task/context/eval IDs and targets/windows were distinct. Per-context logs showed zero correlation mismatches; global interleaving in one PID was expected. No cross-attribution, checkpoint/persistence collision or process error observed. This supports context isolation but does not prove secret non-leakage because key values were correctly not inspected. PID/listener remained healthy under observed parallel calls/threads.

No further poll, payload/secret access, mutation, restart or invocation occurred.
