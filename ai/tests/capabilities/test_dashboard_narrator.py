"""Tests for the Dashboard narrator — the LLM stays bounded, fail-safe to templates.

No real model is called: a fake structured-output runnable is injected. Verifies
that (1) a well-behaved model yields ``generated_by='llm'``, (2) any model error
falls back to the exact templates, and (3) a wrong step count is rejected.
"""

from __future__ import annotations

from shb.capabilities.dashboard.narrator import (
    DashboardFacts,
    StepFact,
    narrate_dashboard,
)


class _FakeRunnable:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    async def ainvoke(self, _messages):
        if self._error is not None:
            raise self._error
        return self._result


class _Result:
    def __init__(self, step_summaries, overall_narrative):
        self.step_summaries = step_summaries
        self.overall_narrative = overall_narrative


def _facts() -> DashboardFacts:
    return DashboardFacts(
        steps=[
            StepFact(1, "Hồ sơ", "Tài sản A."),
            StepFact(2, "Định giá", "Giá 4 tỷ."),
        ],
        overall_template="Kết luận X.",
    )


async def test_narrator_uses_llm_when_model_ok():
    """A valid model response is used and tagged generated_by='llm'."""
    fake = _FakeRunnable(_Result(["Hồ sơ tài sản A đã đủ.", "Giá trị 4 tỷ."], "Kết luận X mượt."))
    out = await narrate_dashboard(_facts(), narrator=fake)
    assert out.generated_by == "llm"
    assert out.step_summaries[0] == (1, "Hồ sơ tài sản A đã đủ.")
    assert out.overall_narrative == "Kết luận X mượt."


async def test_narrator_failsafe_on_error():
    """Any model error returns the exact templates (numbers preserved)."""
    fake = _FakeRunnable(error=RuntimeError("boom"))
    out = await narrate_dashboard(_facts(), narrator=fake)
    assert out.generated_by == "template"
    assert out.step_summaries == [(1, "Tài sản A."), (2, "Giá 4 tỷ.")]
    assert out.overall_narrative == "Kết luận X."


async def test_narrator_rejects_wrong_step_count():
    """A response with the wrong number of steps is rejected → templates."""
    fake = _FakeRunnable(_Result(["only one"], "overall"))
    out = await narrate_dashboard(_facts(), narrator=fake)
    assert out.generated_by == "template"


async def test_narrator_empty_steps_is_template():
    """No steps → template path, no model call needed."""
    out = await narrate_dashboard(DashboardFacts(steps=[], overall_template="none"))
    assert out.generated_by == "template"
