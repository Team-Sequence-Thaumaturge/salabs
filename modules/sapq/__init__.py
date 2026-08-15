"""
SAPQ (Sequence Autonomic Parsing & QA) Master Engine Package v2.0
- 4-Tier Contradiction Matrix & Dual-LLM AST Audit Engine
- Level 1: Structural & Topological Placement Contradiction (TORSION_CROSSING, GHOST_NODE)
- Level 2: Semantic State & Tensor Matrix Contradiction (INTERLOCK_DESYNC)
- Level 3: Asynchronous Event Loop Timing Contradiction (RACE_CONDITION)
- Level 4: User Intent & Spec Alignment Contradiction (INTENT_MISMATCH, INDEX_DESYNC)
- Phase 14: Systemic Causality & Inter-Site Flow Dependency Engine (CAUSALITY_CONTRADICTION)
- Phase 15: Anti-Mockup & Real-Implementation Depth Engine (MOCKUP_HALLUCINATION, SCOPE_REDUCTION)
- Phase 16: Full ESTree AST Node Tree Decomposition & Dual-LLM AI-to-AI Cross-Auditor (SAPQ v2.0)
"""

from .sapq_engine import SAPQEngine, audit_file, audit_directory
from .sapq_ast_parser import ASTParser
from .sapq_llm_auditor import DualLLMAuditor
from .sapq_causality import CausalityContradictionEngine
from .sapq_anti_mockup import AntiMockupDepthEngine
from .sapq_preflight import SAPQPreflightGuard
from .sapq_checkpoint import CheckpointManager
from .sapq_logger import SAPQLogger
from .sapq_arbiter import SAPQArbiter

__version__ = "2.0.0"
__all__ = [
    "SAPQEngine",
    "ASTParser",
    "DualLLMAuditor",
    "CausalityContradictionEngine",
    "AntiMockupDepthEngine",
    "SAPQPreflightGuard",
    "CheckpointManager",
    "SAPQLogger",
    "SAPQArbiter",
    "audit_file",
    "audit_directory"
]
