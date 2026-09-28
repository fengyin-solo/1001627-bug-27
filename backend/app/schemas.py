"""接口出入参模型：列表分页、动作结果与各模块的明细结构。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    size: int = 20
    stats: dict[str, int] | None = None


class ActionResult(BaseModel):
    ok: bool
    message: str
    entry: dict[str, Any] | None = None


class EntryPayload(BaseModel):
    """登记或修改一条业务记录时提交的字段集合。"""

    values: dict[str, Any] = Field(default_factory=dict)
    remark: str | None = None



class FlightEntry(BaseModel):
    """航班计划明细结构。"""

    field_0: str | None = None  # 航班号
    field_1: str | None = None  # 执行日期
    field_2: str | None = None  # 机型
    field_3: str | None = None  # 起降性质
    field_4: str | None = None  # 计划时刻
    field_5: str | None = None  # 预计时刻
    field_6: str | None = None  # 保障等级
    field_7: str | None = None  # 航班状态

class StandEntry(BaseModel):
    """机位明细结构。"""

    field_0: str | None = None  # 机位编号
    field_1: str | None = None  # 机位类别
    field_2: str | None = None  # 所属区域
    field_3: str | None = None  # 适用机型
    field_4: str | None = None  # 廊桥配置
    field_5: str | None = None  # 加注接口
    field_6: str | None = None  # 保障能力
    field_7: str | None = None  # 机位状态

class ApronEntry(BaseModel):
    """巡查单明细结构。"""

    field_0: str | None = None  # 巡查单号
    field_1: str | None = None  # 巡查区域
    field_2: str | None = None  # 巡查人员
    field_3: str | None = None  # 巡查日期
    field_4: str | None = None  # 巡查项目
    field_5: str | None = None  # 发现问题数
    field_6: str | None = None  # 巡查时长
    field_7: str | None = None  # 巡查状态

class BridgeEntry(BaseModel):
    """对接任务明细结构。"""

    field_0: str | None = None  # 对接单号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 廊桥编号
    field_3: str | None = None  # 对接时刻
    field_4: str | None = None  # 撤桥时刻
    field_5: str | None = None  # 操作人员
    field_6: str | None = None  # 对接结果
    field_7: str | None = None  # 对接状态

class DeicingEntry(BaseModel):
    """除冰单明细结构。"""

    field_0: str | None = None  # 除冰单号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 除冰方式
    field_3: str | None = None  # 除冰液用量
    field_4: str | None = None  # 作业车辆
    field_5: str | None = None  # 作业人员
    field_6: str | None = None  # 完成时刻
    field_7: str | None = None  # 除冰状态

class FuelingEntry(BaseModel):
    """加注单明细结构。"""

    field_0: str | None = None  # 加注单号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 加注车号
    field_3: str | None = None  # 加注油量
    field_4: str | None = None  # 油品规格
    field_5: str | None = None  # 加注人员
    field_6: str | None = None  # 完成时刻
    field_7: str | None = None  # 加注状态

class BaggageEntry(BaseModel):
    """装卸单明细结构。"""

    field_0: str | None = None  # 装卸单号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 行李件数
    field_3: str | None = None  # 装卸车辆
    field_4: str | None = None  # 作业班组
    field_5: str | None = None  # 开始时刻
    field_6: str | None = None  # 完成时刻
    field_7: str | None = None  # 装卸状态

class CargoEntry(BaseModel):
    """装载单明细结构。"""

    field_0: str | None = None  # 装载单号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 货邮重量
    field_3: str | None = None  # 装载位置
    field_4: str | None = None  # 装载车辆
    field_5: str | None = None  # 作业人员
    field_6: str | None = None  # 完成时刻
    field_7: str | None = None  # 装载状态

class CateringEntry(BaseModel):
    """配餐单明细结构。"""

    field_0: str | None = None  # 配餐单号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 餐食份数
    field_3: str | None = None  # 餐食类别
    field_4: str | None = None  # 配餐车辆
    field_5: str | None = None  # 送达时刻
    field_6: str | None = None  # 接收人员
    field_7: str | None = None  # 配餐状态

class ShuttleEntry(BaseModel):
    """摆渡任务明细结构。"""

    field_0: str | None = None  # 任务编号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 车辆编号
    field_3: str | None = None  # 乘客人数
    field_4: str | None = None  # 出发时刻
    field_5: str | None = None  # 到达时刻
    field_6: str | None = None  # 驾驶人员
    field_7: str | None = None  # 摆渡状态

class TowingEntry(BaseModel):
    """牵引任务明细结构。"""

    field_0: str | None = None  # 牵引编号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 牵引车号
    field_3: str | None = None  # 起点机位
    field_4: str | None = None  # 终点机位
    field_5: str | None = None  # 牵引人员
    field_6: str | None = None  # 完成时刻
    field_7: str | None = None  # 牵引状态

class LoadsheetEntry(BaseModel):
    """配载单明细结构。"""

    field_0: str | None = None  # 配载单号
    field_1: str | None = None  # 关联航班
    field_2: str | None = None  # 计算重量
    field_3: str | None = None  # 重心位置
    field_4: str | None = None  # 油量数据
    field_5: str | None = None  # 配载人员
    field_6: str | None = None  # 复核人员
    field_7: str | None = None  # 配载状态

class PermitEntry(BaseModel):
    """通行证件明细结构。"""

    field_0: str | None = None  # 证件编号
    field_1: str | None = None  # 持证人员
    field_2: str | None = None  # 所属单位
    field_3: str | None = None  # 通行区域
    field_4: str | None = None  # 有效期至
    field_5: str | None = None  # 发证人员
    field_6: str | None = None  # 发证日期
    field_7: str | None = None  # 证件状态

class GseEntry(BaseModel):
    """保障车辆明细结构。"""

    field_0: str | None = None  # 车辆编号
    field_1: str | None = None  # 车辆类别
    field_2: str | None = None  # 适用作业
    field_3: str | None = None  # 停放区域
    field_4: str | None = None  # 上次保养日
    field_5: str | None = None  # 下次保养日
    field_6: str | None = None  # 责任人
    field_7: str | None = None  # 车辆状态

class SafetyEntry(BaseModel):
    """监察记录明细结构。"""

    field_0: str | None = None  # 监察编号
    field_1: str | None = None  # 监察区域
    field_2: str | None = None  # 监察事项
    field_3: str | None = None  # 违规情形
    field_4: str | None = None  # 涉及单位
    field_5: str | None = None  # 监察人员
    field_6: str | None = None  # 监察日期
    field_7: str | None = None  # 监察状态

class AgreementEntry(BaseModel):
    """保障协议明细结构。"""

    field_0: str | None = None  # 协议编号
    field_1: str | None = None  # 服务单位
    field_2: str | None = None  # 保障项目
    field_3: str | None = None  # 协议金额
    field_4: str | None = None  # 服务期限
    field_5: str | None = None  # 签订人员
    field_6: str | None = None  # 到期日期
    field_7: str | None = None  # 协议状态

class SettlementEntry(BaseModel):
    """结算单明细结构。"""

    field_0: str | None = None  # 结算单号
    field_1: str | None = None  # 关联协议
    field_2: str | None = None  # 结算周期
    field_3: str | None = None  # 应付金额
    field_4: str | None = None  # 已付金额
    field_5: str | None = None  # 审核人员
    field_6: str | None = None  # 付款日期
    field_7: str | None = None  # 结算状态

class TrainingEntry(BaseModel):
    """培训记录明细结构。"""

    field_0: str | None = None  # 培训编号
    field_1: str | None = None  # 培训主题
    field_2: str | None = None  # 培训对象
    field_3: str | None = None  # 授课人员
    field_4: str | None = None  # 培训课时
    field_5: str | None = None  # 考核成绩
    field_6: str | None = None  # 培训日期
    field_7: str | None = None  # 培训状态
