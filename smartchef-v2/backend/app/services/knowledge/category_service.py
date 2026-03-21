"""Knowledge category CRUD with tree structure support."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.api_response import BusinessException
from app.models.knowledge import KnowledgeCategory, KnowledgeDocument
from app.schemas.knowledge import CreateCategoryRequest, UpdateCategoryRequest


async def list_categories_tree(db: AsyncSession) -> list[dict]:
    """Return all categories as a nested tree."""
    result = await db.execute(
        select(KnowledgeCategory).options(selectinload(KnowledgeCategory.children))
    )
    all_cats = result.scalars().unique().all()

    doc_counts = {}
    count_result = await db.execute(
        select(
            KnowledgeDocument.category_id,
            func.count(KnowledgeDocument.id),
        )
        .where(KnowledgeDocument.category_id.isnot(None))
        .group_by(KnowledgeDocument.category_id)
    )
    for cat_id, cnt in count_result.all():
        doc_counts[cat_id] = cnt

    cat_map: dict[UUID, dict] = {}
    for cat in all_cats:
        cat_map[cat.id] = _to_dict(cat, doc_count=doc_counts.get(cat.id, 0))

    roots = []
    for cat in all_cats:
        node = cat_map[cat.id]
        if cat.parent_id and cat.parent_id in cat_map:
            cat_map[cat.parent_id]["children"].append(node)
        else:
            roots.append(node)

    roots.sort(key=lambda n: n["sort_order"])
    return roots


async def create_category(
    db: AsyncSession, data: CreateCategoryRequest, user_id: str,
) -> dict:
    if data.parent_id:
        parent = await db.get(KnowledgeCategory, data.parent_id)
        if not parent:
            raise BusinessException("E60101", "父分类不存在")

    cat = KnowledgeCategory(
        name=data.name,
        description=data.description,
        parent_id=data.parent_id,
        sort_order=data.sort_order,
        created_by=user_id,
    )
    db.add(cat)
    await db.flush()
    return _to_dict(cat)


async def update_category(
    db: AsyncSession, category_id: UUID, data: UpdateCategoryRequest,
) -> dict:
    cat = await db.get(KnowledgeCategory, category_id)
    if not cat:
        raise BusinessException("E60101", "分类不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "parent_id" in update_data and update_data["parent_id"]:
        if update_data["parent_id"] == category_id:
            raise BusinessException("E60101", "分类不能设置自身为父分类")
        parent = await db.get(KnowledgeCategory, update_data["parent_id"])
        if not parent:
            raise BusinessException("E60101", "父分类不存在")

    for key, val in update_data.items():
        setattr(cat, key, val)

    await db.flush()
    return _to_dict(cat)


async def delete_category(db: AsyncSession, category_id: UUID) -> None:
    cat = await db.get(KnowledgeCategory, category_id)
    if not cat:
        raise BusinessException("E60101", "分类不存在")

    child_count = (
        await db.execute(
            select(func.count())
            .select_from(KnowledgeCategory)
            .where(KnowledgeCategory.parent_id == category_id)
        )
    ).scalar() or 0
    if child_count > 0:
        raise BusinessException("E60102", "该分类下存在子分类，无法删除")

    doc_count = (
        await db.execute(
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(KnowledgeDocument.category_id == category_id)
        )
    ).scalar() or 0
    if doc_count > 0:
        raise BusinessException("E60103", "该分类下存在文档，无法删除")

    await db.delete(cat)
    await db.flush()


def _to_dict(cat: KnowledgeCategory, *, doc_count: int = 0) -> dict:
    return {
        "id": str(cat.id),
        "name": cat.name,
        "description": cat.description,
        "parent_id": str(cat.parent_id) if cat.parent_id else None,
        "sort_order": cat.sort_order,
        "created_by": str(cat.created_by) if cat.created_by else None,
        "created_at": cat.created_at.isoformat() if cat.created_at else None,
        "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
        "children": [],
        "document_count": doc_count,
    }
