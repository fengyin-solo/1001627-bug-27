"""通行证件业务规则：区域归属、状态流转、到期判定与统计口径都收在这里。"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.accounts import Operator
from app.store import store

MODULE = "permit"
FIELD_NAMES = ["证件编号", "持证人员", "所属单位", "通行区域", "有效期至", "发证人员", "发证日期"]
REQUIRED_FIELDS = ["证件编号", "持证人员", "所属单位", "通行区域"]
STATUS_ORDER = ["待发证", "有效使用", "已过期", "已注销"]
ACTION_RULES = {"签发证件": "有效使用", "标记过期": "已过期", "注销证件": "已注销"}
NEGATIVE_ACTIONS = []
EXPIRE_SOON_DAYS = 30
DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d")


class PermissionDeniedError(Exception):
    """账号对证件所属通行区域没有管理权限，只读允许、改动拒绝。"""


def _parse_expiry(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _scope_text(operator: Operator) -> str:
    return "全部通行区域" if operator.is_admin else "、".join(operator.areas)


class PermitService:
    # ---- 归属过滤与到期判定 ---------------------------------------------

    def _scoped_rows(self, operator: Operator, today: date) -> list[dict[str, Any]]:
        """只取账号可管通行区域下的证件；按 id 去重，避免同一条在列表里重复出现。"""
        rows: list[dict[str, Any]] = []
        seen: set[int] = set()
        for row in store.rows(MODULE):
            entry_id = int(row.get("id", 0))
            if entry_id in seen:
                continue
            self._normalize(row, today)
            if not operator.can_manage_area(row.get("通行区域")):
                continue
            seen.add(entry_id)
            rows.append(self._present(row))
        return rows

    def normalize_all(self) -> None:
        """把到期判定应用到全部证件；供跨模块看板在统计前统一口径。"""
        today = date.today()
        for row in store.rows(MODULE):
            self._normalize(row, today)

    def _normalize(self, row: dict[str, Any], today: date) -> dict[str, Any]:
        """有效期至早于当前日期的「有效使用」证件一律落为「已过期」。

        列表、明细、统计、签发都走这一处判定，保证各入口口径一致；
        待发证、已注销的证件不被到期判定改动。
        """
        if row.get("status") == "有效使用":
            expiry = _parse_expiry(row.get("有效期至"))
            if expiry is not None and expiry < today:
                row["status"] = "已过期"
                row["pending"] = False
        return row

    def _present(self, row: dict[str, Any]) -> dict[str, Any]:
        """表格直接展示的「证件状态」与内部流转状态保持同步。"""
        row["证件状态"] = row.get("status")
        return row

    # ---- 列表与统计 -----------------------------------------------------

    def list_entries(
        self,
        operator: Operator,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = self._scoped_rows(operator, date.today())
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("证件编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def stats(self, operator: Operator) -> list[dict[str, Any]]:
        """统计口径与列表同源：同样按可管区域归属过滤、按到期判定后的状态计数。"""
        today = date.today()
        soon_deadline = today + timedelta(days=EXPIRE_SOON_DAYS)
        valid = expiring = expired = revoked = 0
        for row in self._scoped_rows(operator, today):
            if row.get("status") == "有效使用":
                valid += 1
                expiry = _parse_expiry(row.get("有效期至"))
                if expiry is not None and today <= expiry <= soon_deadline:
                    expiring += 1
            elif row.get("status") == "已过期":
                expired += 1
            elif row.get("status") == "已注销":
                revoked += 1
        return [
            {"label": "有效证件", "value": valid},
            {"label": "即将过期", "value": expiring},
            {"label": "已过期证件", "value": expired},
            {"label": "已注销证件", "value": revoked},
        ]

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        row = store.find(MODULE, entry_id)
        if row is None:
            return None
        return self._present(self._normalize(row, date.today()))

    # ---- 登记与流转 -----------------------------------------------------

    def create_entry(
        self, values: dict[str, Any], operator: Operator
    ) -> tuple[dict[str, Any] | None, str | None]:
        missing = [
            field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()
        ]
        if missing:
            return None, f"缺少必填字段：{'、'.join(missing)}"

        area = str(values.get("通行区域") or "").strip()
        if not operator.can_manage_area(area):
            raise PermissionDeniedError(
                f"账号「{operator.name}」可管范围为{_scope_text(operator)}，"
                f"不能登记通行区域「{area}」的证件"
            )

        permit_no = str(values.get("证件编号") or "").strip()
        if any(str(row.get("证件编号") or "").strip() == permit_no for row in store.rows(MODULE)):
            return None, f"证件编号 {permit_no} 已存在，证件编号不能重复，登记按失败处理"

        rows = store.rows(MODULE)
        entry: dict[str, Any] = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        for field in FIELD_NAMES:
            entry[field] = str(values.get(field) or "").strip()
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        entry["证件状态"] = entry["status"]
        rows.append(entry)
        return entry, None

    def run_action(
        self, entry_id: int, action: str, operator: Operator
    ) -> tuple[dict[str, Any] | None, str]:
        row = store.find(MODULE, entry_id)
        if row is None:
            return None, f"通行证件 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于通行证件可执行范围"

        area = str(row.get("通行区域") or "").strip()
        if not operator.can_manage_area(area):
            raise PermissionDeniedError(
                f"账号「{operator.name}」可管范围为{_scope_text(operator)}，"
                f"无权{action}通行区域「{area}」下的证件 {row.get('证件编号', entry_id)}，"
                "该证件当前仅可查看"
            )

        today = date.today()
        self._normalize(row, today)

        note = ""
        if action == "签发证件":
            if not str(row.get("持证人员") or "").strip():
                return None, "持证人员为空，不能签发；请先补全持证人员后再提交"
            row["status"] = "有效使用"
            # 待发证证件不会被 _normalize 预判，这里签发后再统一走一次到期口径
            expiry = _parse_expiry(row.get("有效期至"))
            if expiry is not None and expiry < today:
                row["status"] = "已过期"
                note = f"，但有效期至 {expiry.isoformat()} 已过，证件按已过期处理"
        else:
            target = ACTION_RULES[action]
            if target not in STATUS_ORDER:
                return None, f"目标状态「{target}」不在允许的状态序列里"
            row["status"] = target

        row["pending"] = row["status"] in ("待发证", "有效使用")
        row["abnormal"] = action in NEGATIVE_ACTIONS
        self._present(row)
        return row, f"通行证件已{action}{note}"
