"""TestCase CRUD and import/export."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_response import BusinessException
from app.models.batch_test import TestCase
from app.schemas.batch_test import (
    GenerateCasesRequest,
    TestCaseCreate,
    TestCaseImportItem,
    TestCaseOut,
    TestCaseUpdate,
)


async def list_cases(
    db: AsyncSession,
    batch_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict], int]:
    count_q = select(func.count()).select_from(TestCase).where(TestCase.batch_id == batch_id)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(TestCase)
        .where(TestCase.batch_id == batch_id)
        .order_by(TestCase.sort_order, TestCase.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    cases = result.scalars().all()
    items = [TestCaseOut.model_validate(c).model_dump(mode="json") for c in cases]
    return items, total


async def get_case(db: AsyncSession, case_id: uuid.UUID) -> TestCase:
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    case = result.scalars().first()
    if not case:
        raise BusinessException("E50201", "测试用例不存在", http_status=404)
    return case


async def create_case(db: AsyncSession, batch_id: uuid.UUID, data: TestCaseCreate) -> TestCase:
    case = TestCase(
        id=uuid.uuid4(),
        batch_id=batch_id,
        input_text=data.input_text,
        expected_intent=data.expected_intent,
        expected_slots=data.expected_slots,
        expected_domain=data.expected_domain,
        sort_order=data.sort_order,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


async def create_cases_bulk(
    db: AsyncSession, batch_id: uuid.UUID, items: list[TestCaseImportItem]
) -> int:
    cases = []
    for i, item in enumerate(items):
        cases.append(
            TestCase(
                id=uuid.uuid4(),
                batch_id=batch_id,
                input_text=item.input_text,
                expected_intent=item.expected_intent,
                expected_slots=item.expected_slots,
                expected_domain=item.expected_domain,
                sort_order=i,
            )
        )
    db.add_all(cases)
    await db.flush()
    return len(cases)


async def update_case(db: AsyncSession, case_id: uuid.UUID, data: TestCaseUpdate) -> TestCase:
    case = await get_case(db, case_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(case, key, value)
    await db.flush()
    await db.refresh(case)
    return case


async def delete_case(db: AsyncSession, case_id: uuid.UUID) -> uuid.UUID:
    case = await get_case(db, case_id)
    batch_id = case.batch_id
    await db.delete(case)
    await db.flush()
    return batch_id


async def append_generated_cases(db: AsyncSession, batch_id: uuid.UUID, body: GenerateCasesRequest) -> int:
    """Deterministic stub cases for batch regression / UI coverage (replaces LLM until integrated)."""
    max_sort = (
        await db.execute(
            select(func.coalesce(func.max(TestCase.sort_order), -1)).where(TestCase.batch_id == batch_id),
        )
    ).scalar()
    start = int(max_sort or -1) + 1
    items: list[TestCaseImportItem] = []
    for intent in body.intent_names:
        for j in range(body.samples_per_intent):
            items.append(
                TestCaseImportItem(
                    input_text=f"[AI生成] 「{intent}」测试语料 #{j + 1}",
                    expected_intent=intent,
                    expected_domain="command",
                    expected_slots={},
                ),
            )
    if body.include_knowledge:
        n_k = max(1, min(body.samples_per_intent, 8))
        for j in range(n_k):
            items.append(
                TestCaseImportItem(
                    input_text=f"[AI生成] 知识场景追问 #{j + 1}",
                    expected_intent="knowledge_query",
                    expected_domain="knowledge",
                    expected_slots={},
                ),
            )
    if body.include_chitchat:
        n_c = max(1, min(body.samples_per_intent, 8))
        for j in range(n_c):
            items.append(
                TestCaseImportItem(
                    input_text=f"[AI生成] 闲聊边界 #{j + 1}",
                    expected_intent="chitchat",
                    expected_domain="chitchat",
                    expected_slots={},
                ),
            )
    cases = [
        TestCase(
            id=uuid.uuid4(),
            batch_id=batch_id,
            input_text=item.input_text,
            expected_intent=item.expected_intent,
            expected_slots=item.expected_slots,
            expected_domain=item.expected_domain,
            sort_order=start + i,
        )
        for i, item in enumerate(items)
    ]
    db.add_all(cases)
    await db.flush()
    return len(cases)


async def export_cases(db: AsyncSession, batch_id: uuid.UUID) -> list[dict]:
    query = (
        select(TestCase)
        .where(TestCase.batch_id == batch_id)
        .order_by(TestCase.sort_order, TestCase.created_at)
    )
    result = await db.execute(query)
    cases = result.scalars().all()
    return [
        {
            "input_text": c.input_text,
            "expected_intent": c.expected_intent,
            "expected_slots": c.expected_slots,
            "expected_domain": c.expected_domain,
        }
        for c in cases
    ]
