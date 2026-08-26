# Incident Response

Incident reports document findings, confidence, affected indicators, recommended containment, and the difference between direct observations and inference. Every provider failure or missing credential is a limitation that must remain visible in the final assessment.

Require human approval before irreversible or externally visible actions, including persisting an authoritative incident record, blocking shared infrastructure, deleting artifacts, notifying outside parties, or disabling user access. The approval record should capture the decision, reviewer, and rationale.

When information is unavailable or contradictory, fail safely to an `unknown` verdict and recommend a retry or manual investigation. Reliability controls must never turn an infrastructure failure into a fabricated malicious or benign conclusion.
