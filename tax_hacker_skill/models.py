'''
Author: 嘛的叭卡 xxxxxy_112@163.com
Date: 2026-04-08 15:46:39
LastEditors: 嘛的叭卡 xxxxxy_112@163.com
LastEditTime: 2026-04-08 15:46:48
FilePath: \skill\tax_hacker_skill\models.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from pydantic import BaseModel, Field
from typing import List, Optional

class InvoiceItem(BaseModel):
    """发票/收据中的单项商品信息"""
    name: str = Field(..., description="商品或服务名称")
    price: Optional[float] = Field(None, description="单价或总价")
    quantity: Optional[float] = Field(1.0, description="数量")

class InvoiceData(BaseModel):
    """通用发票/收据结构化数据"""
    invoice_code: Optional[str] = Field(None, description="发票代码")
    invoice_number: Optional[str] = Field(None, description="发票号码")
    date: Optional[str] = Field(None, description="开票日期/交易日期 (建议格式: YYYY-MM-DD)")
    amount: float = Field(..., description="交易总金额/价税合计金额")
    tax_amount: Optional[float] = Field(None, description="税额")
    check_code: Optional[str] = Field(None, description="校验码(通常为后6位或全位)")
    vendor: Optional[str] = Field(None, description="销方/商家名称")
    purchaser: Optional[str] = Field(None, description="购方名称")
    currency: str = Field("CNY", description="货币符号或代码 (如 CNY, USD, EUR)")
    items: List[InvoiceItem] = Field(default_factory=list, description="详细商品列表")
    category: Optional[str] = Field(None, description="交易分类 (如 餐饮, 交通, 办公用品)")
    summary: Optional[str] = Field(None, description="交易摘要/内容简述")
    risk_level: Optional[str] = Field("low", description="风险等级 (low, medium, high)")

