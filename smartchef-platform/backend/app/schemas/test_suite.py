"""测试套件相关 Schema 定义。"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ----- 创建/更新请求 -----

class TestSuiteCreate(BaseModel):
    """创建测试套件请求。"""
    name: str = Field(..., min_length=1, max_length=128)
    profile_id: UUID


class TestSuiteUpdate(BaseModel):
    """更新测试套件请求。"""
    name: str | None = Field(None, min_length=1, max_length=128)


# ----- 响应 -----

class TestCaseInfo(BaseModel):
    """测试用例信息。"""
    id: UUID
    suite_id: UUID
    input_text: str
    expected_intent: str | None
    expected_domain: str | None

    model_config = {"from_attributes": True}


class TestSuiteInfo(BaseModel):
    """测试套件概要。"""
    id: UUID
    name: str
    profile_id: UUID
    case_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TestSuiteDetail(BaseModel):
    """测试套件详情（含用例列表）。"""
    id: UUID
    name: str
    profile_id: UUID
    case_count: int
    cases: list[TestCaseInfo]
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateResponse(BaseModel):
    """生成用例响应。"""
    suite_id: UUID
    case_count: int
    message: str = "测试用例生成成功"


class ExecuteRequest(BaseModel):
    """执行批量测试请求。"""
    accuracy_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    latency_threshold_ms: int = Field(default=200, ge=0)


class ExecuteResponse(BaseModel):
    """执行批量测试响应。"""
    report_id: UUID
    message: str = "批量测试执行完成"


class TestReportDetail(BaseModel):
    """测试报告详情（含分析结果）。"""
    id: UUID
    suite_id: UUID
    total_cases: int
    passed_cases: int
    failed_cases: int
    accuracy: float
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    is_passed: bool
    analysis_report: dict | None
    executed_at: datetime

    model_config = {"from_attributes": True}
