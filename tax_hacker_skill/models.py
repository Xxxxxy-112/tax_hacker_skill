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

class ReceiptItem(BaseModel):
    """收据中的单项商品信息"""
    name: str = Field(..., description="商品或服务名称")
    price: Optional[float] = Field(None, description="单价或总价")
    quantity: Optional[float] = Field(1.0, description="数量")

class ReceiptData(BaseModel):
    """TaxHacker 风格的收据结构化数据"""
    vendor: str = Field(..., description="商家或收款人名称")
    date: Optional[str] = Field(None, description="交易日期 (建议格式: YYYY-MM-DD)")
    total_amount: float = Field(..., description="交易总金额")
    currency: str = Field(..., description="货币符号或代码 (如 CNY, USD, EUR)")
    tax_amount: Optional[float] = Field(None, description="税额 (如 VAT/GST)")
    items: List[ReceiptItem] = Field(default_factory=list, description="详细商品列表")
    category: Optional[str] = Field(None, description="交易分类 (如 餐饮, 交通, 办公用品)")
    project: Optional[str] = Field(None, description="所属项目")
    summary: Optional[str] = Field(None, description="交易摘要/内容简述")
    risk_level: Optional[str] = Field("low", description="风险等级 (low, medium, high)")
