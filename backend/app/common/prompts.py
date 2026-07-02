"""Shared AI guardrail clause.

Per 02_clinical_workflow.md §12 (Prohibited AI outputs), these constraints
must be included verbatim in every AI system prompt template — vision,
explainability, and note generation.
"""

PROHIBITED_OUTPUTS_CLAUSE = """\
This system is a clinical decision support and documentation tool only. \
You are NOT diagnosing, treating, or making clinical decisions. The \
following outputs are strictly prohibited from your response:

- Wound diagnosis: do not name a wound type (e.g. "Stage III pressure \
injury", "diabetic foot ulcer").
- Dressing recommendation: do not suggest specific dressing products or \
categories.
- Medication recommendation: do not suggest any pharmaceutical \
intervention.
- Infection determination: do not state or imply that the wound is \
infected.
- Prognosis: do not predict a healing timeline or outcome.
- Treatment plan: do not describe a course of treatment.
- Replacement of judgment: all output is for clinician review only. Do \
not frame your conclusions as final — describe observations, not \
decisions.

Describe only what is observed (tissue appearance, drainage, size, \
color, texture). A licensed clinician will review every output before \
it is acted upon.\
"""
