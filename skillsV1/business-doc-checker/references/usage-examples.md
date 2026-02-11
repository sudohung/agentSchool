# 使用示例

## 示例1：基础检查

### 用户请求
> 请检查我的业务文档是否完整，是否覆盖了所有核心模块和业务流程。

### 技能执行步骤

#### 1. 获取文档内容
```bash
# 用户提供文档路径
DOC_PATH="docs/业务文档.md"

# 读取文档
Read "docs/业务文档.md"
```

#### 2. 扫描项目代码

**扫描模块划分：**
```bash
# 查找所有Service类
Glob "src/main/java/**/*Service.java"

# 结果可能包括：
# - src/main/java/com/example/service/UserService.java
# - src/main/java/com/example/service/OrderService.java
# - src/main/java/com/example/service/ProductService.java
# - src/main/java/com/example/service/InventoryService.java
# - src/main/java/com/example/service/PaymentService.java
```

**扫描业务流程：**
```bash
# 查找Service层的业务方法
Grep -i "public.*save\|create\|update\|process\|handle" "src/main/java/**/service/**/*.java"

# 识别关键流程方法：
# - UserService.createUser
# - OrderService.createOrder
# - OrderService.cancelOrder
# - InventoryService.deductStock
# - PaymentService.processPayment
```

**扫描API接口：**
```bash
# 查找Controller
Glob "src/main/java/**/controller/**/*.java"

# 提取API路径
Grep "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" "src/main/java/**/controller/**/*.java"

# 识别的API：
# - UserController: GET /api/users/{id}, POST /api/users
# - OrderController: GET /api/orders, POST /api/orders, GET /api/orders/{id}, PUT /api/orders/{id}
# - ProductController: GET /api/products
# - CartController: GET /api/cart, POST /api/cart
# - PaymentController: POST /api/payments
```

**扫描数据表：**
```bash
# 查找实体类
Glob "src/main/java/**/entity/**/*.java"
Glob "src/main/java/**/model/**/*.java"

# 识别的数据表：
# - User, Order, Product, Inventory, Cart, Payment
```

#### 3. 对比检查

**检查模块：**
```bash
# 对于每个Service，检查文档中是否包含
Grep -i "用户\|user" "docs/业务文档.md"  # ✅ 找到
Grep -i "订单\|order" "docs/业务文档.md"  # ✅ 找到
Grep -i "商品\|product" "docs/业务文档.md"  # ✅ 找到
Grep -i "库存\|inventory" "docs/业务文档.md"  # ❌ 未找到
Grep -i "支付\|payment" "docs/业务文档.md"  # ✅ 找到
```

**检查流程：**
```bash
# 对于每个业务流程，检查文档
Grep -i "用户注册\|create.*user" "docs/业务文档.md"  # ✅ 找到
Grep -i "创建订单\|create.*order" "docs/业务文档.md"  # ✅ 找到
Grep -i "取消订单\|cancel.*order" "docs/业务文档.md"  # ❌ 未找到
Grep -i "库存扣减\|deduct.*stock" "docs/业务文档.md"  # ❌ 未找到
Grep -i "支付\|payment" "docs/业务文档.md"  # ✅ 找到
```

**检查API：**
```bash
# 对于每个API，检查文档
Grep -i "GET /api/users" "docs/业务文档.md"  # ✅ 找到
Grep -i "POST /api/users" "docs/业务文档.md"  # ✅ 找到
Grep -i "GET /api/orders" "docs/业务文档.md"  # ✅ 找到
Grep -i "POST /api/orders" "docs/业务文档.md"  # ✅ 找到
Grep -i "GET /api/orders/\{id\}" "docs/业务文档.md"  # ✅ 找到
Grep -i "PUT /api/orders/\{id\}" "docs/业务文档.md"  # ❌ 未找到
```

**检查数据表：**
```bash
# 对于每个表，检查文档
Grep -i "user.*表" "docs/业务文档.md"  # ✅ 找到
Grep -i "order.*表" "docs/业务文档.md"  # ✅ 找到
Grep -i "product.*表" "docs/业务文档.md"  # ✅ 找到
Grep -i "inventory.*表" "docs/业务文档.md"  # ❌ 未找到
```

#### 4. 生成报告

```markdown
# 业务文档完整性检查报告

## 检查概述
- **检查时间**: 2026-02-07
- **文档路径**: docs/业务文档.md
- **项目路径**: ./

## 统计概览
| 检查维度 | 总数 | 已覆盖 | 覆盖率 | 缺失数 |
|---------|------|--------|--------|--------|
| 模块划分 | 5 | 4 | 80% | 1 |
| 业务流程 | 5 | 3 | 60% | 2 |
| API接口 | 8 | 7 | 88% | 1 |
| 数据表 | 6 | 5 | 83% | 1 |
| **总计** | 24 | 19 | 79% | 5 |

## 详细检查结果

### 1. 模块划分 ✅覆盖率: 80%

#### 已覆盖的模块 (4/5)
- ✅ 用户管理模块 (UserService) - 文档第3章有详细说明
- ✅ 订单管理模块 (OrderService) - 文档第4章有职责描述
- ✅ 商品模块 (ProductService) - 文档第2章有功能介绍
- ✅ 支付模块 (PaymentService) - 文档第5章有流程说明

#### 缺失的模块 (1/5)
- ❌ 库存管理模块 (InventoryService) - 文档未提及

---

### 2. 业务流程 ✅覆盖率: 60%

#### 已覆盖的流程 (3/5)
- ✅ 用户注册流程 - 文档第3.2节有流程图
- ✅ 订单创建流程 - 文档第4.3节有详细说明
- ✅ 订单支付流程 - 文档第5.2节有步骤说明

#### 缺失的流程 (2/5)
- ❌ 库存扣减流程 - 文档未描述
- ❌ 订单取消流程 - 文档未描述

---

### 3. API接口 ✅覆盖率: 88%

#### 已覆盖的接口 (7/8)
- ✅ GET /api/users/{id} (UserController)
- ✅ POST /api/users (UserController)
- ✅ GET /api/orders (OrderController)
- ✅ POST /api/orders (OrderController)
- ✅ GET /api/orders/{id} (OrderController)
- ✅ GET /api/products (ProductController)
- ✅ GET /api/cart (CartController)
- ✅ POST /api/cart (CartController)
- ✅ POST /api/payments (PaymentController)

#### 缺失的接口 (1/8)
- ❌ PUT /api/orders/{id} (OrderController) - 文档未记录

---

### 4. 数据表 ✅覆盖率: 83%

#### 已覆盖的数据表 (5/6)
- ✅ user 表 - 文档第6章有结构说明
- ✅ order 表 - 文档第6章有结构说明
- ✅ product 表 - 文档第6章有结构说明
- ✅ cart 表 - 文档第6章有结构说明
- ✅ payment 表 - 文档第6章有结构说明

#### 缺失的数据表 (1/6)
- ❌ inventory 表 - 文档未提及

---

## 建议补充内容

1. **模块说明**
   - 库存管理模块的功能和职责

2. **业务流程**
   - 库存扣减流程的详细步骤
   - 订单取消流程的处理逻辑

3. **API接口**
   - 订单更新接口 (PUT /api/orders/{id}) 的文档

4. **数据表设计**
   - inventory 表的结构说明

## 检查说明
- **检查范围**: 广度优先检查，关注业务范围覆盖度
- **检查方法**: 代码扫描 + 文档关键词匹配
- **覆盖标准**: 文档中有实质性描述即视为已覆盖
```

## 示例2：针对特定模块的检查

### 用户请求
> 请重点检查订单模块的文档是否完整，包括订单相关的业务流程、API接口和数据表。

### 执行步骤

1. **范围限定**：只扫描与订单相关的代码
2. **详细扫描**：
   ```bash
   # 扫描订单相关的Service
   Glob "src/main/java/**/*Order*Service.java"

   # 扫描订单相关的Controller
   Glob "src/main/java/**/*Order*Controller.java"

   # 扫描订单相关的实体
   Glob "src/main/java/**/*Order*.java"
   ```

3. **生成针对性报告**

## 示例3：持续集成场景

### 用户请求
> 我们要定期检查文档完整性，如何自动化这个过程？

### 解决方案

1. **创建检查脚本**：使用这个技能生成检查报告
2. **设定阈值**：如覆盖率低于80%则告警
3. **集成到CI/CD**：
   - 在代码提交时自动检查
   - 生成报告并附加到PR
   - 覆盖率下降时阻止合并
