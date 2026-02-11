# 检查流程详细指南

## 整体检查流程

### 1. 准备阶段

#### 1.1 获取业务文档
- 确认文档路径
- 读取文档全文
- 提取文档结构和关键词

#### 1.2 确认项目根目录
- 识别项目结构
- 确认源码目录（通常为src/main/java）
- 确认文档目录（通常为docs/）

### 2. 扫描代码库

#### 2.1 模块划分扫描
**目标**：识别系统的核心功能模块

**扫描策略**：
```bash
# 扫描Service层（通常是核心模块）
Glob "src/main/java/**/*Service.java"

# 扫描Manager层（管理类）
Glob "src/main/java/**/*Manager.java"

# 扫描Module/Component（组件层）
Glob "src/main/java/**/*Component.java"
Glob "src/main/java/**/*Module.java"
```

**提取信息**：
- 类名（去除Service/Manager后缀）
- 包名（识别模块归属）
- 类注释（如果有业务描述）

**判断核心模块的标准**：
- 在业务流程中被频繁调用
- 包含关键业务逻辑
- 有明确的业务领域命名（如Order、User、Payment）

#### 2.2 业务流程扫描
**目标**：识别核心业务处理流程

**扫描策略**：
```bash
# 扫描Service层的所有类
Glob "src/main/java/**/service/**/*.java"

# 查找带有@Transaction的方法
Grep "@Transactional" "src/main/java/**/service/**/*.java"

# 查找主要的业务方法
Grep "public.*void.*save\|create\|update\|process\|handle" "src/main/java/**/service/**/*.java"
```

**提取信息**：
- 方法名（识别流程动作）
- 方法注释（如果有流程描述）
- 流程调用链（通过方法调用分析）

**判断核心流程的标准**：
- 涉及核心业务操作（创建、更新、处理）
- 有事务注解@Transaction
- 方法命名体现业务动作（saveOrder, processPayment）

#### 2.3 API接口扫描
**目标**：识别系统的对外接口

**扫描策略**：
```bash
# 扫描Controller层
Glob "src/main/java/**/controller/**/*.java"
Glob "src/main/java/**/api/**/*.java"

# 查找RequestMapping/GetMapping/PostMapping
Grep "@RequestMapping\|@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" "src/main/java/**/controller/**/*.java"
```

**提取信息**：
- Controller类名（去除Controller后缀）
- 请求路径（从注解中提取）
- 方法名和参数
- 方法注释

**判断关键API的标准**：
- 提供主要业务功能的接口
- 被外部系统调用的接口
- 高频访问的接口

#### 2.4 数据表扫描
**目标**：识别系统涉及的数据表

**扫描策略**：
```bash
# 扫描Entity/Model/DO
Glob "src/main/java/**/entity/**/*.java"
Glob "src/main/java/**/model/**/*.java"
Glob "src/main/java/**/domain/**/*.java"
Glob "src/main/java/**/pojo/**/*.java"
Glob "src/main/java/**/dto/**/*.java"

# 查找@Table注解
Grep "@Table\|@Entity" "src/main/java/**/*.java"
```

**提取信息**：
- 类名（实体名）
- 表名注解（如果有）
- 主要字段（识别核心数据结构）
- 字段注释

**判断重要数据表的标准**：
- 有@Table/@Entity注解
- 包含核心业务数据
- 有主键和关键业务字段

### 3. 对比检查

#### 3.1 文本关键词匹配
对于每个识别到的业务元素（模块、流程、接口、表），检查文档中是否包含：

**匹配策略**：
1. **精确匹配**：检查类名/模块名是否在文档中
   ```bash
   Grep -i "OrderService" doc.md
   ```

2. **模糊匹配**：检查去掉后缀的名称
   ```bash
   Grep -i "Order" doc.md
   ```

3. **语义匹配**：检查相关业务关键词
   - 如果类名是OrderService，也检查"订单"、"order processing"等

#### 3.2 上下文检查
不仅检查是否存在关键词，还要检查是否有实际的描述：

**存在但描述不足的情况**：
- ✅ "文档提到了'订单模块'"
- ❌ "文档只在目录中列出了'订单'，但没有描述"

**判断标准**：
- 关键词出现的上下文是否有实质性描述
- 是否有段落专门描述该模块/流程/接口
- 描述是否包含功能、作用、使用场景等信息

### 4. 生成报告

#### 4.1 统计信息
```
总模块数: N
文档覆盖: M
覆盖比例: M/N * 100%
缺失数量: N - M
```

#### 4.2 详细列表

**模块划分**：
```
✅ 用户管理模块 (UserService) - 文档第3章有详细描述
✅ 订单管理模块 (OrderService) - 文档第5章有流程说明
❌ 库存管理模块 (InventoryService) - 文档未提及
❌ 物流模块 (LogisticsService) - 文档未提及
```

**业务流程**：
```
✅ 订单创建流程 - 文档第6章有流程图和说明
✅ 订单支付流程 - 文档第7章有详细步骤
❌ 库存扣减流程 - 文档未描述
❌ 订单取消流程 - 文档未描述
```

**API接口**：
```
✅ GET /api/orders - 文档有接口说明和参数
✅ POST /api/orders - 文档有接口说明和示例
❌ PUT /api/orders/{id} - 文档未记录
❌ DELETE /api/orders/{id} - 文档未记录
```

**数据表**：
```
✅ order 表 - 文档第4章有表结构说明
✅ user 表 - 文档第4章有表结构说明
❌ inventory 表 - 文档未提及
❌ order_log 表 - 文档未提及
```

#### 4.3 建议补充
根据缺失项，生成具体的补充建议：

```
## 建议补充内容

1. **模块说明**
   - 库存管理模块的功能和职责
   - 物流模块的处理流程

2. **业务流程**
   - 库存扣减的具体流程和规则
   - 订单取消的业务逻辑和状态流转

3. **API接口**
   - 订单更新接口(PUT /api/orders/{id})的说明
   - 订单删除接口(DELETE /api/orders/{id})的说明

4. **数据表设计**
   - inventory 表的结构和字段说明
   - order_log 表的设计和用途说明
```

## 工具使用示例

### 扫描所有Service类
```bash
# 使用Glob查找所有Service文件
Glob "src/main/java/**/*Service.java"
```

### 检查模块是否在文档中
```bash
# 假设模块名为"UserService"
Grep -i "user" doc.md

# 如果没找到，尝试更宽泛的匹配
Grep -i "用户\|user management" doc.md
```

### 统计结果
```bash
# 计算覆盖比例
总数量 = N
已覆盖 = M
覆盖比例 = (M / N) * 100
```

## 注意事项

1. **避免过度匹配**：通用词汇（如"Service"、"Manager"）不应作为匹配依据
2. **关注核心**：优先检查主要的、频繁使用的模块和接口
3. **语义理解**：理解业务领域的同义词（如"订单"="order"）
4. **忽略测试和工具类**：专注于业务代码，忽略测试类、工具类、配置类
