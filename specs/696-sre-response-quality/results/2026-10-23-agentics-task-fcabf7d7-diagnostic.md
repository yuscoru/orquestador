# Sanitized diagnostic — playbook-para-detonaciones

Read-only query by eval_run_id `769c8ef81cdb4169be1228c1cc890633`; no raw prompt/response/judge text.

All 5 cases scored all five generic rubrics; no missing rubrics or evidence-unavailable cases. Means: `respuesta_relevante` 0.20 ([0,0,0,0,1]); `fidelidad_a_evidencia` 0.20 ([0,0,0,0,1]); `seleccion_herramientas_adecuada` 0.80 ([0,1,1,1,1]); `suficiencia_de_evidencia` 0.40 ([0,0,0,1,1]); `manejo_errores_dependencias` 1.00 ([1,1,1,1,1]). Aggregate response quality 0.52 agrees. Hallucinations valid 4/5, unavailable 1/5; its unavailability causes monitoring `judge_unavailable`, not the response-quality score.

Evidence-based diagnosis: low score is concentrated in relevance, evidence fidelity and evidence sufficiency; tool selection mostly passes and dependency handling passes all. Profile mismatch is not proven. Generic v2.8.0 has agent/grounding-oriented rubrics and no target override exists; playbook-specific reporting/orchestrator semantics might score differently, but content review is required to establish that. No content-level cause can be safely identified from aggregate-only reduction.
