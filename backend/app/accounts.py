"""值班账号与通行区域权限。

通行证件按「通行区域」归属，账号能管哪些区域在这里登记：
- areas 为 None 表示平台管理员，所有区域都可管；
- areas 为具体列表时只能查看、操作这些区域下的证件。

真实项目里这里会换成登录态/权限服务；当前以内置账号配合请求头 X-Operator-Id
演示，缺省回落到平台管理员，避免影响其它模块联调。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Operator:
    operator_id: str
    name: str
    areas: tuple[str, ...] | None  # None 表示可管全部通行区域

    @property
    def is_admin(self) -> bool:
        return self.areas is None

    def can_manage_area(self, area: object) -> bool:
        if self.is_admin:
            return True
        return str(area or "").strip() in self.areas


OPERATORS: dict[str, Operator] = {
    "admin": Operator("admin", "值班管理员", None),
    "terminal": Operator("terminal", "航站楼区证件专员", ("航站楼",)),
    "apron": Operator("apron", "机坪区证件专员", ("机坪",)),
}

DEFAULT_OPERATOR = OPERATORS["admin"]


def resolve_operator(operator_id: str | None) -> Operator:
    """按请求传入的账号标识解析值班账号；无法识别时回落到平台管理员。"""
    if operator_id and operator_id.strip() in OPERATORS:
        return OPERATORS[operator_id.strip()]
    return DEFAULT_OPERATOR
