"""Debug: trace fraudulent boleto through full pipeline."""
import sys
sys.path.insert(0, ".")

from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.stages.extract_stage import ExtractStage
from app.services.pipeline.stages.validate_stage import ValidateStage
from app.services.pipeline.stages.risk_stage import RiskStage
from app.services.scoring.fusion_engine import FusionEngine

pdf_path = r"c:\Users\Alisson Davi\Downloads\BOLETO_FRAUDULENTO_TESTE.pdf"

with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

print(f"PDF size: {len(pdf_bytes)} bytes")

# Full pipeline
ctx = PipelineContext(document_type="boleto", file_bytes=pdf_bytes)

print("\n=== STAGE 2: Extract ===")
ExtractStage()._execute(ctx)
print(f"Text extracted: {len(ctx.extracted_text)} chars")
print(f"First 300 chars: {ctx.extracted_text[:300]}")
print(f"Fields extracted: {ctx.extracted_fields}")

print("\n=== STAGE 3: Validate ===")
ValidateStage()._execute(ctx)
print(f"Evidence after Validate: {len(ctx.evidences)}")
for e in ctx.evidences:
    print(f"  [{e.severity.value.upper()}] {e.code}: {e.description[:100]}")

print("\n=== STAGE 5: Risk ===")
RiskStage()._execute(ctx)
print(f"Evidence after Risk: {len(ctx.evidences)}")

print("\n=== FUSION ENGINE ===")
fusion = FusionEngine()
result = fusion.fuse(ctx.evidences)
print(f"Score: {result['final_score']}/100")
print(f"Level: {result['final_level']}")
for c in result["contributions"]:
    print(f"  +{c.contribution:.1f} = {c.evidence_code} (src={c.source} x{c.multiplier})")
