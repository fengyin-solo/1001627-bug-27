"""通行证件接口：维护通行证件，覆盖签发证件、标记过期、注销证件等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.access import AccessContext, get_access_context
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.permit import PermitService

router = APIRouter(prefix="/api/permit", tags=["通行证件"])

service = PermitService()

LIST_FIELDS = ["证件编号", "持证人员", "所属单位", "通行区域", "有效期至", "发证人员", "发证日期", "证件状态"]
STATUSES = ["待发证", "有效使用", "已过期", "已注销"]
SERVICE_REQUIRED_FIELDS = set(service.required_fields)


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按证件编号检索"),
    status: str | None = Query(default=None, description="待发证、有效使用、已过期、已注销"),
    page: int = 1,
    size: int = 20,
    access_context: AccessContext = Depends(get_access_context),
) -> PageResult[dict]:
    """按账号可管区域、证件编号与状态过滤通行证件列表；统计口径与列表一致。"""
    if page < 1 or size < 1:
        raise HTTPException(status_code=400, detail="分页参数必须大于 0")
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    items, total = service.list_entries(
        keyword=keyword,
        status=status,
        page=page,
        size=size,
        access_context=access_context,
    )
    stats = service.summarize(
        service.visible_rows(access_context, keyword=keyword)
    )
    return PageResult(items=items, total=total, page=page, size=size, stats=stats)


@router.get("/export")
def export_entries(
    access_context: AccessContext = Depends(get_access_context),
) -> dict[str, Any]:
    """导出当前账号可管区域内的通行证件清单。"""
    items = service.visible_rows(access_context)
    return {"module": "permit", "total": len(items), "items": items}


@router.get("/{entry_id}", response_model=dict)
def get_entry(
    entry_id: int,
    access_context: AccessContext = Depends(get_access_context),
) -> dict:
    """读取单条通行证件明细；不在可管区域时不暴露证件存在性。"""
    entry = service.get_entry(entry_id, access_context=access_context)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"通行证件 {entry_id} 不存在或不在当前账号可查看范围")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(
    payload: EntryPayload,
    access_context: AccessContext = Depends(get_access_context),
) -> ActionResult:
    """登记一条通行证件，缺字段或编号重复时说明原因而不是静默丢弃。"""
    if access_context.restricted:
        area_text = "、".join(sorted(access_context.managed_areas or [])) or "授权区域"
        raise HTTPException(
            status_code=403,
            detail=f"当前账号仅可查看{area_text}的通行证件，不能登记或变更证件",
        )
    entry, messages = service.create_entry(payload.values, access_context)
    if messages:
        missing = [message for message in messages if message in SERVICE_REQUIRED_FIELDS]
        errors = [message for message in messages if message not in SERVICE_REQUIRED_FIELDS]
        if missing:
            errors.insert(0, f"缺少必填字段：{'、'.join(missing)}")
        return ActionResult(ok=False, message="；".join(errors))
    return ActionResult(ok=True, message="通行证件已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(
    entry_id: int,
    payload: EntryPayload,
    access_context: AccessContext = Depends(get_access_context),
) -> ActionResult:
    """对单条通行证件执行签发证件、标记过期、注销证件；越权动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    if access_context.restricted:
        area_text = "、".join(sorted(access_context.managed_areas or [])) or "授权区域"
        raise HTTPException(
            status_code=403,
            detail=f"当前账号仅可查看{area_text}的通行证件，不能执行「{action}」",
        )
    entry, message = service.run_action(
        entry_id,
        action,
        access_context,
        payload.values,
    )
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
