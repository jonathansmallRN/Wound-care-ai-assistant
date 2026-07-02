"""AI provider abstraction.

When MOCK_AI_MODE=true (default), every method below returns a
deterministic, rule-derived response built from already-known structured
data — no network call, no API key required. When MOCK_AI_MODE=false and
OPENAI_API_KEY is set, the same methods call the real GPT-4.1 model.
Callers (vision/explainability/notes services) never need to know which
branch ran — only this module's internals change between the two modes.
"""

import base64
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI, OpenAIError

from app.common.prompts import PROHIBITED_OUTPUTS_CLAUSE
from app.config import settings


@dataclass
class AICallResult:
    success: bool
    model_version: str
    latency_ms: int
    prompt_sent: str
    response_received: str | None
    data: dict | None
    error_message: str | None = None


def _deterministic_index(seed: str, length: int) -> int:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return int(digest, 16) % length


def _mock_tissue_change(tissue_type: str, seed: str) -> str:
    if tissue_type in ("granulation", "epithelial"):
        return "improved"
    if tissue_type in ("slough", "eschar"):
        return "worsened"
    return ["improved", "stable", "worsened"][_deterministic_index(seed, 3)]


def _mock_drainage_change(drainage_amount: str, drainage_type: str, seed: str) -> str:
    if drainage_amount == "heavy" or drainage_type == "purulent":
        return "worsened"
    if drainage_amount in ("none", "minimal") and drainage_type in ("serous", "serosanguineous"):
        return ["improved", "stable"][_deterministic_index(seed, 2)]
    return "stable"


class AIClient:
    def __init__(self) -> None:
        self._client: OpenAI | None = None
        if not settings.mock_ai_mode and settings.openai_api_key:
            # PHI/BAA notice: wound images and patient measurements are transmitted to
            # OpenAI when MOCK_AI_MODE=false. Ensure a Business Associate Agreement
            # (BAA) with OpenAI is in place before using this with identifiable patient
            # data. See README §"Real OpenAI calls" for details.
            self._client = OpenAI(api_key=settings.openai_api_key)

    @property
    def mock_mode(self) -> bool:
        return self._client is None

    def analyze_wound_image(
        self,
        *,
        assessment_id: str,
        image_path: str | None,
        tissue_type: str,
        drainage_amount: str,
        drainage_type: str,
        periwound: str,
    ) -> AICallResult:
        system_prompt = (
            f"{PROHIBITED_OUTPUTS_CLAUSE}\n\n"
            "You are the vision analysis stage of a wound care assistant. "
            "Describe the wound image only. Respond with strict JSON: "
            '{"vision_output": "<2-3 sentence visual description>", '
            '"tissue_change": "improved"|"stable"|"worsened", '
            '"drainage_change": "improved"|"stable"|"worsened"}. '
            "tissue_change and drainage_change describe the visual trend versus "
            "the prior assessment, not a diagnosis."
        )
        user_prompt = (
            f"Clinician-entered context for this assessment: tissue_type={tissue_type}, "
            f"drainage_amount={drainage_amount}, drainage_type={drainage_type}, "
            f"periwound={periwound}. Analyze the attached wound image."
        )
        prompt_sent = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"

        if self.mock_mode:
            tissue_change = _mock_tissue_change(tissue_type, assessment_id)
            drainage_change = _mock_drainage_change(drainage_amount, drainage_type, assessment_id)
            vision_output = (
                f"Wound bed shows {tissue_type} tissue. Drainage appears {drainage_amount} "
                f"in amount, {drainage_type} in character. Periwound skin is {periwound}. "
                "Findings are descriptive only and require clinician interpretation."
            )
            data = {
                "vision_output": vision_output,
                "tissue_change": tissue_change,
                "drainage_change": drainage_change,
            }
            return AICallResult(
                success=True,
                model_version="mock-vision-v1",
                latency_ms=0,
                prompt_sent=prompt_sent,
                response_received=json.dumps(data),
                data=data,
            )

        start = time.monotonic()
        try:
            content: list[dict] = [{"type": "text", "text": user_prompt}]
            if image_path and Path(image_path).is_file():
                encoded = base64.b64encode(Path(image_path).read_bytes()).decode()
                mime = "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
                content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}})
            response = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                response_format={"type": "json_object"},
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            text = response.choices[0].message.content or "{}"
            data = json.loads(text)
            return AICallResult(
                success=True,
                model_version=settings.openai_model,
                latency_ms=latency_ms,
                prompt_sent=prompt_sent,
                response_received=text,
                data=data,
            )
        except (OpenAIError, json.JSONDecodeError, KeyError, IndexError) as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            return AICallResult(
                success=False,
                model_version=settings.openai_model,
                latency_ms=latency_ms,
                prompt_sent=prompt_sent,
                response_received=None,
                data=None,
                error_message=str(exc),
            )

    def generate_evidence_narrative(
        self,
        *,
        area_delta_pct: float,
        tissue_change: str,
        drainage_change: str,
    ) -> AICallResult:
        system_prompt = (
            f"{PROHIBITED_OUTPUTS_CLAUSE}\n\n"
            "You are the explainability stage of a wound care assistant. Phrase three "
            "short clinical observation findings (area, tissue, drainage) from the "
            "supplied deltas. Respond with strict JSON: "
            '{"area_finding": "...", "tissue_finding": "...", "drainage_finding": "..."}.'
        )
        user_prompt = (
            f"area_delta_pct={area_delta_pct}, tissue_change={tissue_change}, "
            f"drainage_change={drainage_change}"
        )
        prompt_sent = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"
        mock_data = self._mock_evidence_narrative(area_delta_pct, tissue_change, drainage_change)

        if self.mock_mode:
            return AICallResult(
                success=True,
                model_version="mock-explainability-v1",
                latency_ms=0,
                prompt_sent=prompt_sent,
                response_received=json.dumps(mock_data),
                data=mock_data,
            )

        start = time.monotonic()
        try:
            response = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            text = response.choices[0].message.content or "{}"
            data = json.loads(text)
            return AICallResult(
                success=True,
                model_version=settings.openai_model,
                latency_ms=latency_ms,
                prompt_sent=prompt_sent,
                response_received=text,
                data=data,
            )
        except (OpenAIError, json.JSONDecodeError) as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            # Narrative phrasing is non-blocking — fall back to the same
            # deterministic templates used in mock mode so the clinician
            # is never blocked by an explainability AI failure.
            return AICallResult(
                success=False,
                model_version=settings.openai_model,
                latency_ms=latency_ms,
                prompt_sent=prompt_sent,
                response_received=None,
                data=mock_data,
                error_message=str(exc),
            )

    @staticmethod
    def _mock_evidence_narrative(area_delta_pct: float, tissue_change: str, drainage_change: str) -> dict:
        direction = "reduced" if area_delta_pct >= 0 else "increased"
        area_finding = f"Area {direction} {abs(area_delta_pct):.1f}%"
        tissue_phrases = {
            "improved": "Increased granulation tissue",
            "stable": "Tissue appearance unchanged",
            "worsened": "Increased slough or necrotic tissue",
        }
        drainage_phrases = {
            "improved": "Drainage decreased",
            "stable": "Drainage unchanged",
            "worsened": "Drainage increased or character worsened",
        }
        return {
            "area_finding": area_finding,
            "tissue_finding": tissue_phrases.get(tissue_change, "Tissue appearance unchanged"),
            "drainage_finding": drainage_phrases.get(drainage_change, "Drainage unchanged"),
        }

    def generate_progress_note(
        self,
        *,
        assessment_summary: str,
        classification: str | None,
        confidence_tier: str | None,
        vision_output: str | None,
        override_reason: str | None,
    ) -> AICallResult:
        system_prompt = (
            f"{PROHIBITED_OUTPUTS_CLAUSE}\n\n"
            "You are the progress note generation stage of a wound care assistant. "
            "Draft a clinician-editable progress note from the supplied objective "
            "data. Respond with strict JSON: {\"note_draft\": \"...\"}."
        )
        user_prompt = (
            f"{assessment_summary}\nClassification: {classification}\n"
            f"Confidence tier: {confidence_tier}\nVision findings: {vision_output}\n"
            f"Clinician override reason: {override_reason}"
        )
        prompt_sent = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"
        mock_note = self._mock_progress_note(
            assessment_summary, classification, confidence_tier, vision_output, override_reason
        )

        if self.mock_mode:
            return AICallResult(
                success=True,
                model_version="mock-notes-v1",
                latency_ms=0,
                prompt_sent=prompt_sent,
                response_received=json.dumps({"note_draft": mock_note}),
                data={"note_draft": mock_note},
            )

        start = time.monotonic()
        try:
            response = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            text = response.choices[0].message.content or "{}"
            data = json.loads(text)
            return AICallResult(
                success=True,
                model_version=settings.openai_model,
                latency_ms=latency_ms,
                prompt_sent=prompt_sent,
                response_received=text,
                data=data,
            )
        except (OpenAIError, json.JSONDecodeError) as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            return AICallResult(
                success=False,
                model_version=settings.openai_model,
                latency_ms=latency_ms,
                prompt_sent=prompt_sent,
                response_received=None,
                data={"note_draft": mock_note},
                error_message=str(exc),
            )

    @staticmethod
    def _mock_progress_note(
        assessment_summary: str,
        classification: str | None,
        confidence_tier: str | None,
        vision_output: str | None,
        override_reason: str | None,
    ) -> str:
        lines = [assessment_summary]
        if vision_output:
            lines.append(f"AI-assisted findings (clinician-reviewed): {vision_output}")
        if classification:
            lines.append(f"Healing trend: {classification} (confidence: {confidence_tier}).")
        if override_reason:
            lines.append(f"Clinician override note: {override_reason}")
        lines.append(
            "This note reflects observations only and does not constitute a diagnosis, "
            "treatment plan, or prognosis. For clinician documentation and review."
        )
        return "\n".join(lines)


ai_client = AIClient()
