# 报告模板

## 完整性检查报告模板

```markdown
# 业务文档完整性检查报告

## 检查概述

- **检查时间**: ${CHECK_DATE}
- **文档路径**: ${DOC_PATH}
- **项目路径**: ${PROJECT_PATH}

## 统计概览

| 检查维度 | 总数 | 已覆盖 | 覆盖率 | 缺失数 |
|---------|------|--------|--------|--------|
| 模块划分 | ${MODULE_TOTAL} | ${MODULE_COVERED} | ${MODULE_PERCENT}% | ${MODULE_MISSING} |
| 业务流程 | ${FLOW_TOTAL} | ${FLOW_COVERED} | ${FLOW_PERCENT}% | ${FLOW_MISSING} |
| API接口 | ${API_TOTAL} | ${API_COVERED} | ${API_PERCENT}% | ${API_MISSING} |
| 数据表 | ${TABLE_TOTAL} | ${TABLE_COVERED} | ${TABLE_PERCENT}% | ${TABLE_MISSING} |
| **总计** | ${TOTAL} | ${COVERED} | ${OVERALL_PERCENT}% | ${MISSING} |

## 详细检查结果

### 1. 模块划分 ✅覆盖率: ${MODULE_PERCENT}%

#### 已覆盖的模块 (${MODULE_COVERED}/${MODULE_TOTAL})
${MODULE_COVERED_LIST}

#### 缺失的模块 (${MODULE_MISSING}/${MODULE_TOTAL})
${MODULE_MISSING_LIST}

---

### 2. 业务流程 ✅覆盖率: ${FLOW_PERCENT}%

#### 已覆盖的流程 (${FLOW_COVERED}/${FLOW_TOTAL})
${FLOW_COVERED_LIST}

#### 缺失的流程 (${FLOW_MISSING}/${FLOW_TOTAL})
${FLOW_MISSING_LIST}

---

### 3. API接口 ✅覆盖率: ${API_PERCENT}%

#### 已覆盖的接口 (${API_COVERED}/${API_TOTAL})
${API_COVERED_LIST}

#### 缺失的接口 (${API_MISSING}/${API_TOTAL})
${API_MISSING_LIST}

---

### 4. 数据表 ✅覆盖率: ${TABLE_PERCENT}%

#### 已覆盖的数据表 (${TABLE_COVERED}/${TABLE_TOTAL})
${TABLE_COVERED_LIST}

#### 缺失的数据表 (${TABLE_MISSING}/${TABLE_TOTAL})
${TABLE_MISSING_LIST}

---

## 建议补充内容

### 优先级高的补充项

1. **模块说明**
   ${MODULE_SUGGESTIONS}

2. **业务流程**
   ${FLOW_SUGGESTIONS}

3. **API接口**
   ${API_SUGGESTIONS}

4. **数据表设计**
   ${TABLE_SUGGESTIONS}

### 补充建议

- 建议在文档的对应章节补充上述缺失内容
- 对于核心业务模块，建议增加详细的流程图和说明
- 对于关键API接口，建议补充接口文档和调用示例
- 对于重要数据表，建议补充表结构说明和字段含义

## 检查说明

- **检查范围**: 本次检查为广度优先检查，关注业务范围的覆盖度，不深入检查实现细节
- **检查方法**: 通过代码扫描识别核心业务元素，与文档内容进行关键词匹配
- **匹配规则**: 使用精确匹配和语义匹配相结合的方式
- **覆盖标准**: 文档中对该元素有实质性描述即视为已覆盖
```

## 报告项格式说明

### 模块项格式
```
- ✅ ${模块名} (${类名}) - ${文档位置和描述摘要}
- ❌ ${模块名} (${类名}) - 文档未提及
```

### 流程项格式
```
- ✅ ${流程名} - ${文档位置和描述摘要}
- ❌ ${流程名} - 文档未描述
```

### API项格式
```
- ✅ ${HTTP方法} ${路径} (${类名}) - ${文档位置和描述摘要}
- ❌ ${HTTP方法} ${路径} (${类名}) - 文档未记录
```

### 数据表项格式
```
- ✅ ${表名/实体名} - ${文档位置和描述摘要}
- ❌ ${表名/实体名} - 文档未提及
```

## 变量替换说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| ${CHECK_DATE} | 检查日期 | 2026-02-07 |
| ${DOC_PATH} | 文档路径 | docs/README.md |
| ${PROJECT_PATH} | 项目根路径 | ./ |
| ${MODULE_TOTAL} | 模块总数 | 8 |
| ${MODULE_COVERED} | 已覆盖模块数 | 6 |
| ${MODULE_PERCENT} | 模块覆盖率 | 75 |
| ${MODULE_MISSING} | 缺失模块数 | 2 |
| ${MODULE_COVERED_LIST} | 已覆盖模块列表 | (使用模块项格式) |
| ${MODULE_MISSING_LIST} | 缺失模块列表 | (使用模块项格式) |
| ${MODULE_SUGGESTIONS} | 模块补充建议 | "- 库存管理模块的功能和职责说明" |
| ${FLOW_TOTAL} | 流程总数 | 5 |
| ${FLOW_COVERED} | 已覆盖流程数 | 3 |
| ${FLOW_PERCENT} | 流程覆盖率 | 60 |
| ${FLOW_MISSING} | 缺失流程数 | 2 |
| ${FLOW_COVERED_LIST} | 已覆盖流程列表 | (使用流程项格式) |
| ${FLOW_MISSING_LIST} | 缺失流程列表 | (使用流程项格式) |
| ${FLOW_SUGGESTIONS} | 流程补充建议 | "- 库存扣减流程的详细说明" |
| ${API_TOTAL} | API总数 | 10 |
| ${API_COVERED} | 已覆盖API数 | 8 |
| ${API_PERCENT} | API覆盖率 | 80 |
| ${API_MISSING} | 缺失API数 | 2 |
| ${API_COVERED_LIST} | 已覆盖API列表 | (使用API项格式) |
| ${API_MISSING_LIST} | 缺失API列表 | (使用API项格式) |
| ${API_SUGGESTIONS} | API补充建议 | "- 订单更新接口的详细文档" |
| ${TABLE_TOTAL} | 数据表总数 | 6 |
| ${TABLE_COVERED} | 已覆盖数据表数 | 4 |
| ${TABLE_PERCENT} | 数据表覆盖率 | 67 |
| ${TABLE_MISSING} | 缺失数据表数 | 2 |
| ${TABLE_COVERED_LIST} | 已覆盖数据表列表 | (使用数据表项格式) |
| ${TABLE_MISSING_LIST} | 缺失数据表列表 | (使用数据表项格式) |
| ${TABLE_SUGGESTIONS} | 数据表补充建议 | "- inventory表的结构说明" |
| ${TOTAL} | 总检查项数 | 29 |
| ${COVERED} | 总已覆盖项数 | 21 |
| ${OVERALL_PERCENT} | 总体覆盖率 | 72 |
| ${MISSING} | 总缺失项数 | 8 |

## 示例报告

```markdown
# 业务文档完整性检查报告

## 检查概述

- **检查时间**: 2026-02-07
- **文档路径**: docs/业务文档.md
- **项目路径**: ./my-project

## 统计概览

| 检查维度 | 总数 | 已覆盖 | 覆盖率 | 缺失数 |
|---------|------|--------|--------|--------|
| 模块划分 | 8 | 6 | 75% | 2 |
| 业务流程 | 5 | 3 | 60% | 2 |
| API接口 | 10 | 8 | 80% | 2 |
| 数据表 | 6 | 4 | 67% | 2 |
| **总计** | 29 | 21 | 72% | 8 |

## 详细检查结果

### 1. 模块划分 ✅覆盖率: 75%

#### 已覆盖的模块 (6/8)
- ✅ 用户管理模块 (UserService) - 文档第3章有详细的功能说明
- ✅ 订单管理模块 (OrderService) - 文档第4章有模块职责描述
- ✅ 支付模块 (PaymentService) - 文档第5章有支付流程说明
- ✅ 商品模块 (ProductService) - 文档第2章有商品管理介绍
- ✅ 购物车模块 (CartService) - 文档第6章有购物车功能说明
- ✅ 优惠券模块 (CouponService) - 文档第7章有优惠券使用说明

#### 缺失的模块 (2/8)
- ❌ 库存管理模块 (InventoryService) - 文档未提及
- ❌ 物流模块 (LogisticsService) - 文档未提及

---

### 2. 业务流程 ✅覆盖率: 60%

#### 已覆盖的流程 (3/5)
- ✅ 用户注册流程 - 文档第3.2节有流程图和步骤说明
- ✅ 订单创建流程 - 文档第4.3节有完整流程描述
- ✅ 订单支付流程 - 文档第5.2节有支付流程说明

#### 缺失的流程 (2/5)
- ❌ 库存扣减流程 - 文档未描述
- ❌ 订单取消流程 - 文档未描述

---

### 3. API接口 ✅覆盖率: 80%

#### 已覆盖的接口 (8/10)
- ✅ GET /api/users/{id} (UserController) - 文档第8.1节有接口说明
- ✅ POST /api/users (UserController) - 文档第8.2节有接口说明
- ✅ GET /api/orders (OrderController) - 文档第9.1节有接口说明
- ✅ POST /api/orders (OrderController) - 文档第9.2节有接口说明
- ✅ GET /api/orders/{id} (OrderController) - 文档第9.3节有接口说明
- ✅ POST /api/payments (PaymentController) - 文档第10.1节有接口说明
- ✅ GET /api/products (ProductController) - 文档第11.1节有接口说明
- ✅ POST /api/cart (CartController) - 文档第12.1节有接口说明

#### 缺失的接口 (2/10)
- ❌ PUT /api/orders/{id} (OrderController) - 文档未记录
- ❌ DELETE /api/orders/{id} (OrderController) - 文档未记录

---

### 4. 数据表 ✅覆盖率: 67%

#### 已覆盖的数据表 (4/6)
- ✅ user 表 - 文档第13.1节有表结构说明和字段含义
- ✅ order 表 - 文档第13.2节有表结构说明和字段含义
- ✅ product 表 - 文档第13.3节有表结构说明和字段含义
- ✅ cart 表 - 文档第13.4节有表结构说明和字段含义

#### 缺失的数据表 (2/6)
- ❌ inventory 表 - 文档未提及
- ❌ order_log 表 - 文档未提及

---

## 建议补充内容

### 优先级高的补充项

1. **模块说明**
   - 库存管理模块 (InventoryService) 的功能和职责说明
   - 物流模块 (LogisticsService) 的处理流程和接口说明

2. **业务流程**
   - 库存扣减流程的详细步骤和业务规则
   - 订单取消流程的状态流转和处理逻辑

3. **API接口**
   - 订单更新接口 (PUT /api/orders/{id}) 的详细文档
   - 订单删除接口 (DELETE /api/orders/{id}) 的详细文档

4. **数据表设计**
   - inventory 表的结构说明、字段含义和业务用途
   - order_log 表的设计说明和使用场景

### 补充建议

- 建议在文档第4章补充库存管理模块的说明
- 建议在文档第7章补充物流模块的功能介绍
- 建议在文档第4.4节补充订单取消流程的说明
- 建议在文档第9.4节补充订单更新和删除接口的文档
- 建议在文档第13.5节补充inventory表和order_log表的设计说明

## 检查说明

- **检查范围**: 本次检查为广度优先检查，关注业务范围的覆盖度，不深入检查实现细节
- **检查方法**: 通过代码扫描识别核心业务元素，与文档内容进行关键词匹配
- **匹配规则**: 使用精确匹配和语义匹配相结合的方式
- **覆盖标准**: 文档中对该元素有实质性描述即视为已覆盖
```
