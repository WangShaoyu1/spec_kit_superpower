"""测试相关服务：手动测试、批量测试、用例生成、智能分析等。"""
from app.services.testing.manual_test import (
    create_test_session,
    send_message,
    ManualTestChatResult,
)
from app.services.testing.case_generator import (
    generate_test_cases,
    CaseGeneratorStats,
)
from app.services.testing.batch_test import execute_batch_test
from app.services.testing.analyzer import (
    analyze_test_results,
    generate_llm_suggestions,
    AnalysisReport,
)

__all__ = [
    "create_test_session",
    "send_message",
    "ManualTestChatResult",
    "generate_test_cases",
    "CaseGeneratorStats",
    "execute_batch_test",
    "analyze_test_results",
    "generate_llm_suggestions",
    "AnalysisReport",
]
