# 快速开始指南

## 准备工作

1. 确保有Python 3.6+环境
2. 准备一个Java项目（Maven或Gradle项目）
3. 准备一份业务文档（Markdown格式）

## 使用步骤

### 方式1：完整检查流程（推荐）

适合首次使用或全面检查

```bash
# 步骤1: 扫描Java项目
python scripts/java_scanner.py ./my-project

# 步骤2: 手动检查文档覆盖情况
# 根据扫描结果，对照文档检查每个模块、API、数据表是否在文档中

# 步骤3: 生成报告
python scripts/example_usage.py
```

### 方式2：快速检查（自动化）

适合已经熟悉检查流程的用户

```bash
# 一键检查并生成报告
python scripts/quick_check.py docs/业务文档.md ./my-project

# 报告将生成在: docs/文档完整性检查报告.md
```

## 使用示例

### 示例1：检查标准Spring Boot项目

假设项目结构如下：
```
my-project/
├── src/
│   └── main/
│       └── java/
│           └── com/
│               └── example/
│                   ├── controller/
│                   │   ├── UserController.java
│                   │   └── OrderController.java
│                   ├── service/
│                   │   ├── UserService.java
│                   │   └── OrderService.java
│                   └── entity/
│                       ├── User.java
│                       └── Order.java
└── docs/
    └── README.md
```

执行检查：
```bash
cd my-project
python /path/to/scripts/quick_check.py docs/README.md .
```

### 示例2：只生成报告（已有检查结果）

如果已经手动检查过，可以直接生成报告：

```bash
# 编辑 scripts/example_usage.py，修改其中的数据
# 然后运行：
python scripts/example_usage.py
```

## 检查项说明

### 1. 模块划分
- **检查范围**: 所有 `*Service.java` 和 `*Manager.java` 文件
- **匹配策略**:
  - 检查模块名（如 "User"）
  - 检查类名（如 "UserService"）
  - 检查常见中文关键词（如 "用户管理"）

### 2. 业务流程
- **检查范围**: Service层的公共业务方法
- **匹配策略**: 人工检查文档是否描述了这些流程

### 3. API接口
- **检查范围**: 所有 `*Controller.java` 中的 `@GetMapping`、`@PostMapping` 等注解
- **匹配策略**:
  - 检查API路径（如 "/api/users"）
  - 检查控制器名（如 "UserController"）

### 4. 数据表
- **检查范围**: Entity/Model/Domain等目录下的实体类
- **匹配策略**:
  - 检查实体名（如 "User"）
  - 检查表名（如 "@Table(name="user")"）

## 输出文件

检查完成后会生成 `文档完整性检查报告.md`，包含：
- 统计概览（覆盖率、缺失数）
- 详细检查结果（已覆盖和缺失项）
- 建议补充内容

## 常见问题

### Q: 扫描结果包含太多不重要的类？
A: 可以手动过滤，只保留核心业务模块

### Q: 检查结果不够准确？
A: 脚本使用关键词匹配，复杂场景需要人工复查

### Q: 如何自定义检查规则？
A: 编辑 `quick_check.py` 中的 `contains_keyword` 方法

## 下一步

1. 阅读检查报告，了解文档缺失的内容
2. 根据建议补充文档
3. 再次运行检查，验证补充效果
4. 将检查集成到CI/CD流程中（可选）
