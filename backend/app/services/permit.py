"""通行证件业务规则：状态流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.access import AccessContext
from app.store import store

MODULE = "permit"
REQUIRED_FIELDS = ["证件编号", "持证人员", "所属单位", "通行区域", "有效期至"]
OPTIONAL_FIELDS = ["发证人员", "发证日期"]
PENDING_ISSUE = "待发证"
ACTIVE = "有效使用"
EXPIRED = "已过期"
CANCELLED = "已注销"
STATUS_ORDER = [PENDING_ISSUE, ACTIVE, EXPIRED, CANCELLED]
ACTION_RULES = {"签发证件": ACTIVE, "标记过期": EXPIRED, "注销证件": CANCELLED}
NEGATIVE_ACTIONS = []


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _parse_date(value: Any) -> date | None:
    text = _clean(value)
    if len(text) != 10:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


class PermitService:
    required_fields = REQUIRED_FIELDS

    def visible_rows(
        self,
        access_context: AccessContext | None = None,
        *,
        keyword: str | None = None,
        status: str | None = None,
        today: date | None = None,
        normalize: bool = True,
    ) -> list[dict[str, Any]]:
        """按账号可管区域取得证件；所有列表、导出和统计都从这里取数。"""
        current_day = today or date.today()
        rows = []
        for row in store.rows(MODULE):
            area = _clean(row.get("通行区域"))
            if access_context is not None and not access_context.can_view_area(area):
                continue
            if normalize:
                row = self.display_row(row, today=current_day)
            if keyword and keyword not in _clean(row.get("证件编号")):
                continue
            if status and row.get("status") != status:
                continue
            rows.append(row)
        return rows

    def summarize(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        """统计与列表同源：先按账号区域过滤，再统计各状态数量。"""
        counts = {label: 0 for label in STATUS_ORDER}
        for row in rows:
            label = row.get("status")
            if label in counts:
                counts[label] += 1
        return counts

    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
        access_context: AccessContext | None = None,
        today: date | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = self.visible_rows(
            access_context,
            keyword=keyword,
            status=status,
            today=today,
        )
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(
        self,
        entry_id: int,
        *,
        access_context: AccessContext | None = None,
        today: date | None = None,
    ) -> dict[str, Any] | None:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None
        entry = self.display_row(entry, today=today or date.today())
        if access_context is not None and not access_context.can_view_area(
            _clean(entry.get("通行区域"))
        ):
            return None
        return entry

    def can_access_entry(self, entry: dict[str, Any], access_context: AccessContext) -> bool:
        return access_context.can_view_area(_clean(entry.get("通行区域")))

    def display_row(
        self,
        entry: dict[str, Any],
        *,
        today: date | None = None,
    ) -> dict[str, Any]:
        """列表/统计使用的视图数据，不把日期判断产生的状态写回仓库。"""
        return self.normalize_row(dict(entry), today=today)

    def normalize_row(
        self,
        entry: dict[str, Any],
        *,
        today: date | None = None,
    ) -> dict[str, Any]:
        """已注销以人工注销为准；其他证件一旦超过有效期即落为已过期。"""
        current_day = today or date.today()
        if entry.get("status") != CANCELLED:
            expiry = _parse_date(entry.get("有效期至"))
            if expiry is not None and expiry < current_day:
                entry["status"] = EXPIRED
        status = str(entry.get("status") or PENDING_ISSUE)
        entry["status"] = status
        entry["pending"] = status == PENDING_ISSUE
        entry["abnormal"] = status == EXPIRED
        entry["证件状态"] = status
        return entry

    def create_entry(
        self,
        values: dict[str, Any],
        access_context: AccessContext | None = None,
        *,
        today: date | None = None,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        if access_context is not None and access_context.restricted:
            return None, ["当前账号仅可查看授权通行区域的证件，不能登记或变更证件"]

        missing = [field for field in REQUIRED_FIELDS if not _clean(values.get(field))]
        if missing:
            return None, missing

        expiry = _parse_date(values.get("有效期至"))
        if expiry is None:
            return None, ["有效期至必须是 YYYY-MM-DD 格式的有效日期"]

        permit_number = _clean(values.get("证件编号"))
        if any(_clean(row.get("证件编号")) == permit_number for row in store.rows(MODULE)):
            return None, [f"证件编号 {permit_number} 已存在，不能重复登记"]

        current_day = today or date.today()
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        for field in [*REQUIRED_FIELDS, *OPTIONAL_FIELDS]:
            value = _clean(values.get(field))
            if value:
                entry[field] = value
        entry["有效期至"] = expiry.isoformat()
        entry["status"] = EXPIRED if expiry < current_day else PENDING_ISSUE
        entry["pending"] = entry["status"] != EXPIRED
        entry["abnormal"] = entry["status"] == EXPIRED
        entry["证件状态"] = entry["status"]
        rows.append(entry)
        return entry, []

    def run_action(
        self,
        entry_id: int,
        action: str,
        access_context: AccessContext | None = None,
        values: dict[str, Any] | None = None,
        *,
        today: date | None = None,
    ) -> tuple[dict[str, Any] | None, str]:
        current_day = today or date.today()
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"通行证件 {entry_id} 不存在或已归档"
        if access_context is not None and not self.can_access_entry(entry, access_context):
            area = _clean(entry.get("通行区域"))
            scope_label = "授权" if access_context.restricted else "可管理"
            return None, f"证件归属通行区域为{area}，不在当前账号{scope_label}范围内"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于通行证件可执行范围"
        if access_context is not None and access_context.restricted:
            area = _clean(entry.get("通行区域"))
            return None, f"当前账号仅可查看{area or '授权区域'}的证件，不能执行「{action}」"

        entry = self.normalize_row(entry, today=current_day)

        target = ACTION_RULES[action]
        expiry = _parse_date(entry.get("有效期至"))
        if action == "签发证件":
            if not _clean(entry.get("持证人员")):
                return None, "持证人员为空，不能签发通行证件"
            if expiry is None:
                return None, "有效期至不是 YYYY-MM-DD 格式的有效日期，不能签发"
            if expiry < current_day:
                return None, f"有效期至 {expiry.isoformat()} 已过，证件已过期，不能签发"
            issuer = _clean((values or {}).get("发证人员"))
            if not issuer and access_context is not None:
                issuer = _clean(access_context.account)
            if issuer:
                entry["发证人员"] = issuer
            issue_date_text = _clean((values or {}).get("发证日期"))
            issue_date = _parse_date(issue_date_text) if issue_date_text else current_day
            if issue_date is None:
                return None, "发证日期必须是 YYYY-MM-DD 格式的有效日期"
            entry["发证日期"] = issue_date.isoformat()

        entry["status"] = target
        entry["pending"] = False
        entry["abnormal"] = target == EXPIRED
        entry["证件状态"] = target
        return entry, f"通行证件已{action}"
