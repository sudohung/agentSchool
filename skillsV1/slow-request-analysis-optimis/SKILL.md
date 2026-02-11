---
name: slow-request-analysis-optimis
description: SOP for analyzing and optimizing slow API endpoints using only code analysis (no external tools).
---

# 慢请求分析与优化 SOP

## 适用场景

当收到慢接口列表，需要通过代码分析定位性能问题并设计优化方案时使用。

## 必需输入

- 慢接口列表: HTTP方法 + 路径
- 代码入口点 (Controller/Router 类名 + 方法名)

## 必须输出

1. **优先级排序的接口列表** (Top N)
2. **每个接口的分析报告** (使用下方模板，必须包含精确代码位置)
3. **验证计划**
4. **回滚方案**

## SOP 流程

### Step 1: 建立工作清单并排优先级

| 接口 | 症状 | 业务影响 | 瓶颈类型 | 入口模块 |
|------|------|----------|----------|----------|
| GET /api/xxx | 稳定慢/间歇慢 | 核心/管理/批量 | DB/外调/CPU/锁 | XxxController |

**排序规则**: 业务影响高 > 复用度高 > 稳定慢优先

### Step 2: 快速扫描 (每接口15-30分钟)

从 Controller 向下追踪，检查以下问题模式：

| 问题类型 | 典型模式 |
|----------|----------|
| **数据规模** | 无界查询、内存全量过滤/排序、List.contains热循环 |
| **I/O模式** | 循环调用DAO/Client(N+1)、重复相同参数调用、可并行的串行调用 |
| **事务/锁** | 事务范围过大、粗粒度synchronized、重试放大延迟 |
| **缓存机会** | 字典数据每次请求、请求内重复查询、缓存击穿风险 |

### Step 3: 深度分析 (Top 接口)

产出调用链、数据流、瓶颈假设 (详见报告模板)

### Step 4: 设计优化方案

| 风险级别 | 优化手段 |
|----------|----------|
| **Tier 1 (低风险)** | 消除重复调用、请求级缓存、N+1改批量、加分页/限制、提前返回 |
| **Tier 2 (中风险)** | 并行化独立调用、短TTL进程内缓存、缩小事务边界 |
| **Tier 3 (高风险)** | 异步卸载、读写分离、分片 |

### Step 5: 验证与回滚

- **正确性**: 单元测试 + 集成测试
- **性能代理**: DAO/Client调用次数、复杂度改善
- **回滚**: Feature Flag 开关

## 分析报告模板 (必须使用)

```markdown
## 接口: <METHOD> <PATH>
入口: `<包名.ControllerClass#method>` (<文件路径>:<行号>)

### 调用链
1. `ControllerClass#method` → `ServiceA#methodA` (文件路径:行号)
2. `ServiceA#methodA` → `RepositoryX#query` (文件路径:行号)
3. ...

### 数据流
- N = <描述> (来源: 参数/用户范围/租户规模)
- M = <描述>

### 问题定位 (按影响排序)

#### 问题1: <问题类型> - <严重程度: 高/中/低>
**位置**: `<包名.类名#方法名>` (<文件路径>:<起始行>-<结束行>)
**问题代码**:
​```java
// 文件路径:行号
<精简的问题代码片段，不超过10行>
​```
**原因**: <为什么慢>
**触发条件**: <什么情况下会慢，数据规模>
**影响**: <调用次数/耗时估算>

#### 问题2: ...

### 优化方案

#### Tier 1 (低风险) - 预期效果: <量化描述>
**修改位置**: `<类名#方法名>` (<文件路径>:<行号>)
**当前代码**:
​```java
<当前问题代码>
​```
**优化后**:
​```java
<优化后代码>
​```
**风险**: <一致性/顺序/内存等风险>

#### Tier 2 (中风险) - 预期效果: ...
...

### 验证计划
- [ ] 单元测试: <测试点>
- [ ] 性能代理: <调用次数从X降到Y>

### 回滚方案
- Feature Flag: `<flag名称>`
- 回滚操作: <具体步骤>
```

## 示例

```markdown
## 接口: GET /api/orders
入口: `com.example.controller.OrderController#listOrders` (src/main/java/com/example/controller/OrderController.java:45)

### 调用链
1. `OrderController#listOrders` → `OrderService#queryOrders` (OrderService.java:78)
2. `OrderService#queryOrders` → `OrderRepository#findByUserId` (OrderService.java:82)
3. `OrderService#queryOrders` → 循环调用 `ProductClient#getProduct` (OrderService.java:89)

### 数据流
- N = 订单数量 (来源: 用户历史订单，平均200，最大5000)
- M = 每订单商品数 (平均3)

### 问题定位

#### 问题1: N+1查询 - 高
**位置**: `com.example.service.OrderService#queryOrders` (OrderService.java:87-92)
**问题代码**:
​```java
// OrderService.java:87-92
for (Order order : orders) {  // orders.size() = N
    Product product = productClient.getProduct(order.getProductId()); // 每次远程调用
    order.setProductName(product.getName());
}
​```
**原因**: 循环内逐个调用远程服务
**触发条件**: N > 50 时明显变慢
**影响**: 远程调用从1次变为N次，N=200时约2秒

### 优化方案

#### Tier 1 - 预期效果: 远程调用从N次降为1次
**修改位置**: `OrderService#queryOrders` (OrderService.java:87-92)
**当前代码**:
​```java
for (Order order : orders) {
    Product product = productClient.getProduct(order.getProductId());
    order.setProductName(product.getName());
}
​```
**优化后**:
​```java
Set<Long> productIds = orders.stream().map(Order::getProductId).collect(toSet());
Map<Long, Product> productMap = productClient.batchGetProducts(productIds);
for (Order order : orders) {
    Product product = productMap.get(order.getProductId());
    order.setProductName(product != null ? product.getName() : "");
}
​```
**风险**: 需确认productClient支持批量接口

### 验证计划
- [ ] 单元测试: 空订单、单订单、多订单场景
- [ ] 性能代理: productClient调用次数从N降为1

### 回滚方案
- Feature Flag: `feature.order.batch-product-query`
- 回滚操作: 关闭flag即可回退到逐个查询
```

## 关键原则

1. **精确定位**: 必须给出 `文件路径:行号` 格式的精确位置
2. **代码为证**: 每个问题必须附带实际问题代码片段
3. **量化影响**: 用调用次数、复杂度、数据量等可度量指标
4. **最小改动**: 优先Tier 1方案，一个PR只解决一个核心问题
5. **可回滚**: 非trivial改动必须有Feature Flag
