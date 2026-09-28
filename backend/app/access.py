"""请求账号的访问上下文。

当前项目还没有完整登录态，区域权限先通过请求头传入：
- X-Account-Name：当前账号名称；
- X-Managed-Areas：账号可查看的通行区域，多个区域用逗号分隔；
- X-Managed-Areas: * 表示不受区域限制。

未传 X-Managed-Areas 时保持兼容，视为全区域管理员。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class AccessContext:
    account: str | None = None
    managed_areas: frozenset[str] | None = None

    @property
    def restricted(self) -> bool:
        """受限账号只有查看权限，不能登记、签发、标记或注销证件。"""
        return self.managed_areas is not None

    def can_view_area(self, area: str | None) -> bool:
        if self.managed_areas is None:
            return True
        return str(area or "").strip() in self.managed_areas


def get_access_context(request: Request) -> AccessContext:
    headers = request.headers
    account = (
        headers.get("x-account-name")
        or headers.get("x-account")
        or headers.get("x-user-name")
    )
    raw_areas = (
        headers.get("x-managed-areas")
        or headers.get("x-manage-areas")
        or headers.get("x-permit-areas")
        or headers.get("x-access-areas")
        or headers.get("x-allowed-areas")
        or headers.get("x-areas")
    )
    if raw_areas is None:
        return AccessContext(account=account, managed_areas=None)
    if raw_areas.strip() == "*":
        return AccessContext(account=account, managed_areas=None)

    areas = frozenset(
        part.strip() for part in re.split(r"[,，;；、]+", raw_areas) if part.strip()
    )
    return AccessContext(account=account, managed_areas=areas)
