"""通行证件接口：维护通行证件，覆盖签发证件、标记过期、注销证件等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query

from app.accounts import Operator, resolve_operator
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.permit import PermissionDeniedError, PermitService

router = APIRouter(prefix="/api/permit", tags=["通行证件"])

service = PermitService()


def _operator(operator_id: str | None) -> Operator:
    """从请求头 X-Operator-Id 识别值班账号；导出等浏览器直开场景再走查询参数。"""
    return resolve_operator(operator_id)


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按证件编号检索"),
    status: str | None = Query(default=None, description="待发证、有效使用、已过期、已注销"),
    page: int = 1,
    size: int = 20,
    operator_id: str | None = Query(default=None, alias="operatorId"),
    x_operator_id: str | None = Header(default=None, alias="X-Operator-Id"),
) -> PageResult[dict]:
    """按账号可管通行区域归属过滤后，再按证件编号与状态检索；没有数据时返回空页。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    operator = _operator(x_operator_id or operator_id)
    items, total = service.list_entries(
        operator, keyword=keyword, status=status, page=page, size=size
    )
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/stats")
def entry_stats(
    operator_id: str | None = Query(default=None, alias="operatorId"),
    x_operator_id: str | None = Header(default=None, alias="X-Operator-Id"),
) -> dict[str, Any]:
    """通行证件统计：口径与列表一致，均按账号可管区域与到期后的实际状态计数。"""
    operator = _operator(x_operator_id or operator_id)
    return {"items": service.stats(operator)}


@router.get("/export")
def export_entries(
    operator_id: str | None = Query(default=None, alias="operatorId"),
    x_operator_id: str | None = Header(default=None, alias="X-Operator-Id"),
) -> dict[str, Any]:
    """导出通行证件清单：只导出当前账号可管通行区域下的全量数据。"""
    operator = _operator(x_operator_id or operator_id)
    items, total = service.list_entries(operator, page=1, size=10000)
    return {"module": "permit", "total": total, "items": items}


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条通行证件明细；不存在时给出可读的错误说明。明细不受区域限制，只读。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"通行证件 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(
    payload: EntryPayload,
    x_operator_id: str | None = Header(default=None, alias="X-Operator-Id"),
) -> ActionResult:
    """登记一条通行证件，缺字段或证件编号重复时说明原因而不是静默丢弃。"""
    operator = _operator(x_operator_id)
    try:
        entry, message = service.create_entry(payload.values, operator)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if message:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message="通行证件已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(
    entry_id: int,
    payload: EntryPayload,
    x_operator_id: str | None = Header(default=None, alias="X-Operator-Id"),
) -> ActionResult:
    """对单条通行证件执行签发证件、标记过期、注销证件；越区与非法动作会被拦下并说明原因。"""
    operator = _operator(x_operator_id)
    action = str(payload.values.get("action") or "").strip()
    try:
        entry, message = service.run_action(entry_id, action, operator)
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
