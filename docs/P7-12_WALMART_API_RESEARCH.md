# Walmart Marketplace API 调研报告

**日期：** 2026-09-18  
**任务：** P7-12 Walmart API 调研（只读优先）

## 1. Walmart Marketplace API 概述

### 1.1 API 类型
- **Marketplace API**: 第三方卖家 API（主要目标）
- **Supplier API**: 供应商 API（不适用）
- **Affiliate API**: 联盟营销 API（可选）

### 1.2 认证方式
- **OAuth 2.0**: 客户端凭证流
- **WM_SVC.NAME**: 服务名称头
- **WM_QOS.CORRELATION_ID**: 请求关联 ID
- **Authorization**: Bearer token

### 1.3 API 端点（只读）
```
Base URL: https://marketplace.walmart.com/mp/v4/

订单：
- GET /orders/list - 订单列表
- GET /orders/{purchaseOrderId} - 订单详情

商品：
- GET /items - 商品列表
- GET /items/{sku} - 商品详情

库存：
- GET /inventory - 库存查询

价格：
- GET /prices - 价格查询

报告：
- GET /reports - 报告列表
```

## 2. 与 Amazon/Shopify 对比

| 特性 | Amazon SP-API | Shopify | Walmart |
|------|--------------|---------|---------|
| 认证 | OAuth 2.0 + LWA | OAuth 2.0 | OAuth 2.0 |
| 速率限制 | 2 req/sec | 4 req/sec | 调用限制严格 |
| 数据格式 | JSON | JSON | JSON |
| 分页 | nextToken | cursor | offset/limit |
| 沙盒 | 有 | 有 | 有 |
| 文档质量 | 优秀 | 优秀 | 一般 |

## 3. 可行性评估

### 3.1 优势
- ✅ 标准 RESTful API
- ✅ JSON 数据格式
- ✅ OAuth 2.0 认证
- ✅ 有沙盒环境
- ✅ 只读操作足够（订单、商品、库存）

### 3.2 挑战
- ⚠️ API 调用限制较严格
- ⚠️ 文档不如 Amazon/Shopify 完善
- ⚠️ 需要卖家账号才能访问沙盒
- ⚠️ 部分端点需要特殊权限

### 3.3 风险
- 🔴 审批流程较长（可能需要数周）
- 🟡 速率限制可能影响批量操作
- 🟡 某些高级功能需要额外申请

## 4. 实施计划

### Phase 1: Mock 适配器（1-2 天）
- 创建 WalmartClient 骨架
- 实现 mock 数据（订单、商品）
- 单元测试覆盖

### Phase 2: 真实 API 集成（3-5 天）
- OAuth 2.0 认证流程
- 订单/商品 API 调用
- 错误处理和重试
- 集成测试

### Phase 3: 高级功能（2-3 天）
- 库存查询
- 价格查询
- 报告生成

## 5. 数据模型设计

```python
@dataclass
class WalmartOrder:
    purchase_order_id: str
    order_status: str
    order_date: str
    shipping_info: dict
    order_lines: list[WalmartOrderLine]

@dataclass
class WalmartOrderLine:
    line_number: int
    sku: str
    product_name: str
    quantity: int
    unit_price: str
    currency: str = "USD"

@dataclass
class WalmartItem:
    sku: str
    product_name: str
    brand: str
    price: str
    currency: str = "USD"
    stock: int
    category: str
```

## 6. 结论

**建议：** 继续实施，优先实现只读功能（订单、商品）

**理由：**
1. API 标准且文档可用
2. 与现有架构兼容
3. Mock 优先策略降低风险
4. 只读操作满足首期需求

**下一步：**
- P7-13: 创建 Walmart 适配器（mock + 真实 API 预留）
- P7-14: 统一平台适配器接口重构
- P7-15: P7-MS2 验收
