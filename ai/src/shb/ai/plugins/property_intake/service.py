"""property_intake AI service (async, file-accepting).

Thin adapter: validates input, delegates to the LangGraph pipeline, returns the
form-ready :class:`PropertyIntakeOutput`. Auto-discovered by the plugin registry.
"""

from __future__ import annotations

from shb.ai.plugins.base import AIServiceContext, AIServiceMeta, BaseAIService
from shb.ai.plugins.property_intake.graph import run_intake
from shb.ai.plugins.property_intake.schema import (
    PropertyIntakeInput,
    PropertyIntakeOutput,
)


class PropertyIntakeService(BaseAIService):
    """Extract property documents and auto-fill the 'Nhập thông tin' form."""

    meta = AIServiceMeta(
        id="property_intake",
        name="Trích xuất hồ sơ bất động sản",
        description=(
            "Trích xuất thông tin từ sổ đỏ/sổ hồng, tờ khai lệ phí trước bạ, "
            "biên bản bàn giao, thông báo thuế đất và tự điền vào biểu mẫu nhập thông tin."
        ),
        version="0.1.0",
        is_async=True,
        accepts_file=True,
        file_types=["pdf", "docx"],
    )

    InputSchema = PropertyIntakeInput
    OutputSchema = PropertyIntakeOutput

    async def run(
        self, input_data: PropertyIntakeInput, ctx: AIServiceContext
    ) -> PropertyIntakeOutput:
        """Run the extraction pipeline for the given uploaded files."""
        return await run_intake(input_data, ctx)
