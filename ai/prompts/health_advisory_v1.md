# health_advisory v1

Write a short public health advisory for residents of {place}.
Structured context (observed + forecast; do not add numbers that are not here):
{context_json}

Requirements:
- Simple, calm, non-alarming language for the general public (reading age ~12).
- `category` must be exactly the supplied current category.
- 3-5 practical protective steps (e.g. limit outdoor exertion, N95 masks outdoors, keep windows
  closed at night, check on elderly neighbours). No medical diagnosis, no product brands.
- sensitive_groups: one sentence for children, elderly, pregnant people and people with heart or
  lung conditions.
- Do not mention likely polluters or enforcement actions.
- Write in English; translation happens in a separate step.

Return only JSON matching the response schema.
