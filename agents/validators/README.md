# Multi-Agent Document Validation System

A sophisticated system that uses 10 specialized agents to validate technical documentation against actual source code.

## 🎯 Purpose

This system ensures that business analysis documents, API specifications, and architecture designs remain synchronized with actual code implementation. It identifies inconsistencies, missing implementations, and documentation errors through automated multi-agent collaboration.

## 🏗️ Architecture

### System Overview

```
User Request
    ↓
┌─────────────────────────────────────┐
│  Coordinator Agent                  │
│  (Orchestrator & Aggregator)        │
└─────────────────────────────────────┘
    ↓ (Parallel Invocation)
    ├─→ Entity Validator          (Domain models)
    ├─→ ER Diagram Validator      (ER diagrams)
    ├─→ API Validator             (REST endpoints)
    ├─→ Method Validator          (Service methods)
    ├─→ State Validator           (State machines)
    ├─→ Flow Validator            (Business flows)
    ├─→ DataFlow Validator        (Data transformations)
    ├─→ Reference Validator       (File/class references)
    └─→ Structure Validator       (Document completeness)
    ↓ (Results Collection)
┌─────────────────────────────────────┐
│  Final Validation Report            │
│  (Chinese, actionable insights)     │
└─────────────────────────────────────┘
```

## 🤖 Agent Roles

### Coordinator Agent (`coordinator.agent.md`)
- **Role**: Orchestrator
- **Responsibilities**:
  - Analyze target documents
  - Generate task files for expert agents
  - Invoke 10 expert agents in parallel
  - Aggregate results and resolve conflicts
  - Generate final comprehensive report

### Expert Agents

| Agent | File | Responsibility | Typical Items |
|-------|------|----------------|---------------|
| Entity Validator | `entity-validator.md` | Validate entity models vs code classes | Fields, types, relationships |
| ER Diagram Validator | `er-diagram-validator.md` | Validate Mermaid ER diagrams vs JPA entities | ER entities, fields, relationships |
| API Validator | `api-validator.md` | Validate API endpoints vs Controllers | HTTP methods, paths, parameters |
| Method Validator | `method-validator.md` | Validate method signatures vs Services | Method names, parameters, returns |
| State Validator | `state-validator.md` | Validate state machines vs code logic | States, transitions, events |
| Flow Validator | `flow-validator.md` | Validate business flows vs implementation | Sequence diagrams, call chains |
| DataFlow Validator | `dataflow-validator.md` | Validate data transformations | Data mappings, conversions |
| Reference Validator | `reference-validator.md` | Validate file/class path references | Package names, file paths |
| Structure Validator | `structure-validator.md` | Validate document completeness | Sections, consistency, standards |

## 📁 Directory Structure

```
.github/validators/              # Agent configuration files
├── README.md                    # This file
├── doc-validation-coordinator.md # Coordinator agent (1200+ lines)
├── entity-validator.md          # Entity validation (280 lines)
├── er-diagram-validator.md      # ER diagram validation (NEW)
├── api-validator.md             # API validation (300 lines)
├── method-validator.md          # Method validation (280 lines)
├── state-validator.md           # State machine validation (260 lines)
├── flow-validator.md            # Business flow validation (340 lines)
├── dataflow-validator.md        # Data flow validation (360 lines)
├── reference-validator.md       # Reference validation (200 lines)
└── structure-validator.md       # Structure validation (220 lines)

.doc-validator/                  # Shared knowledge base
├── workspace/                   # Active validation sessions
│   └── session_YYYYMMDD_HHMMSS/
│       ├── tasks/              # Task files (coordinator → experts)
│       │   ├── entity-validation-task.md
│       │   ├── er-diagram-validation-task.md
│       │   ├── api-validation-task.md
│       │   └── ... (10 task files)
│       ├── results/            # Result files (experts → coordinator)
│       │   ├── entity-validation-result.md
│       │   ├── er-diagram-validation-result.md
│       │   ├── api-validation-result.md
│       │   └── ... (10 result files)
│       └── FINAL_REPORT.md     # Aggregated report (Chinese)
├── history/                    # Archived validation sessions
├── config/                     # Configuration files
└── templates/                  # Standard templates
    ├── task-template.md        # Task file format
    ├── er-diagram-validation-task-template.md # ER diagram task template
    └── result-template.md      # Result file format
```

## 🔄 Workflow

### Phase 1: Initialization (Coordinator)
1. User provides document path
2. Coordinator creates session directory: `.doc-validator/workspace/session_<timestamp>/`
3. Coordinator analyzes document structure

### Phase 2: Task Distribution (Coordinator)
4. Extract validation items from document (entities, ER diagrams, APIs, methods, etc.)
5. Generate up to 10 task files in `tasks/` directory
6. Each task file contains specific checklist for that validation dimension

### Phase 3: Parallel Execution (Up to 10 Expert Agents)
7. Coordinator invokes expert agents in **parallel** (single message, multiple Task tool calls)
8. Each expert agent:
   - Reads its assigned task file
   - Uses Glob/Read/Grep to find and analyze source code
   - Validates each checklist item
   - Calculates confidence scores (0.0-1.0)
   - Writes result file to `results/` directory

### Phase 4: Aggregation (Coordinator)
9. Coordinator collects result files from all executed agents
10. Resolves conflicts using **expert priority strategy**
11. Generates final comprehensive report in Chinese
12. Archives session to `history/` directory

## 📋 Communication Protocol

### Task File Format

Task files are created by coordinator for each expert agent:

```markdown
# [Validation Type] Task List

## Task Metadata
- **Task ID**: unique-identifier
- **Session ID**: session_YYYYMMDD_HHMMSS
- **Document Path**: path/to/document.md
- **Creation Time**: YYYY-MM-DD HH:MM:SS
- **Assigned Agent**: [agent-name]-validator

## Task Description
Brief description of validation scope

## Validation Checklist

### Item 1: [Name]
- **Document Location**: Line XXX-YYY
- **Expected Code Location**: package.ClassName
- **Key Attributes**: [attributes to verify]
- **Validation Criteria**: [specific checks]

### Item 2: [Name]
...

## Reference Information
- **Project Root**: E:\workspace\xpproject\xp-dragon-mmp
- **Source Code Paths**: src/main/java/...
```

### Result File Format

Result files are created by expert agents:

```markdown
# [Validation Type] Result Report

**Agent**: [agent-name]-validator
**Execution Time**: YYYY-MM-DD HH:MM:SS
**Duration**: X.XX seconds
**Confidence**: 0.XX
**Status**: SUCCESS / FAILED / PARTIAL

## Execution Summary
- **Total Items**: XX
- **Passed**: XX
- **Failed**: XX
- **Uncertain**: XX

## Detailed Results

### ✅ PASS: [Item Name]
- **Document Location**: document.md:123
- **Code Location**: src/main/java/Example.java:45
- **Confidence**: 0.95
- **Details**: All attributes match perfectly

### ❌ FAIL: [Item Name]
- **Document Location**: document.md:456
- **Code Location**: NOT_FOUND
- **Confidence**: 0.90
- **Issue**: Class does not exist in codebase
- **Suggestion**: Create the class or update documentation

### ⚠️ UNCERTAIN: [Item Name]
- **Confidence**: 0.65
- **Reason**: Type mismatch - needs manual review

## Expert Opinion
[Domain-specific insights and recommendations]

## Execution Log
[Detailed execution trace for debugging]
```

## 🎯 Key Features

### 1. Expert Priority Conflict Resolution

When agents disagree:
- **Domain expert opinion** takes precedence
- Example: Entity Validator opinion on entity issues > other agents
- High confidence scores > low confidence scores
- Conservative approach: any failure → warning flag

### 2. Maximum Fault Tolerance

- Individual agent failure doesn't stop the process
- Continue with available results
- Clear error reporting for failed dimensions
- Graceful degradation

### 3. Parallel Execution

- Up to 10 expert agents can run simultaneously (based on document content)
- Typical execution time: 8-12 minutes for large documents
- Coordinator uses single message with multiple Task tool calls

### 4. Confidence Scoring

Each validation result includes objective confidence score (0.0-1.0):
- **0.90-1.00**: High confidence (perfect match or clear mismatch)
- **0.70-0.89**: Medium confidence (minor discrepancies)
- **0.00-0.69**: Low confidence (needs human review)

### 5. Actionable Insights

Every failure includes:
- Specific file:line references
- Clear description of the issue
- Concrete suggestion for fix
- Link to relevant code section

## 🚀 Usage

### Basic Usage

```
User: Validate the business logic document at 2026doc/mmpAnalysis/analysis_results/business_logic.md
```

The coordinator will automatically:
1. Analyze the document
2. Generate task files
3. Invoke expert agents in parallel (based on document content)
4. Aggregate results
5. Generate final report

### Output Location

Final report: `.doc-validator/workspace/session_<timestamp>/FINAL_REPORT.md`

### Example Report Statistics

```
## Validation Summary
- Total items checked: 156
- Passed: 142 (91.0%)
- Failed: 9 (5.8%)
- Uncertain: 5 (3.2%)
- Average confidence: 0.87
```

## 📊 Validation Dimensions

| Dimension | What We Check | Code Artifacts | Tools Used |
|-----------|--------------|----------------|------------|
| **Entity Models** | Fields, types, relationships | Entity classes, JPA annotations | Glob, Read, Regex |
| **ER Diagrams** | Mermaid ER entities, fields, relationships | JPA Entity classes, annotations | Read, Glob, Regex |
| **API Interfaces** | Endpoints, methods, params | @RestController, @RequestMapping | Grep, Read |
| **Method Signatures** | Method names, params, returns | Service classes, public methods | Glob, Read, Regex |
| **State Machines** | States, transitions, events | Enum, state fields, logic | Grep, Read |
| **Business Flows** | Sequence diagrams, call chains | Service method calls, flow logic | Grep, Read |
| **Data Flows** | Data transformations | Mapper classes, converters | Glob, Grep |
| **References** | File paths, class names | Package structure, imports | Glob, Bash |
| **Structure** | Document completeness | N/A (document-only check) | Read, Regex |

## ⚙️ Configuration

### Customization Points

1. **Validation Rules**: Edit individual agent config files
2. **Confidence Thresholds**: Adjust in agent `confidence_calculation` sections
3. **Report Language**: Currently Chinese, can be customized in coordinator
4. **Task Templates**: Modify `.doc-validator/templates/*.md`

### Adding New Validation Dimensions

To add a new validator:
1. Create `new-validator.agent.md` following existing patterns
2. Update coordinator to generate task file for new validator
3. Add new agent to parallel invocation list
4. Update result aggregation logic

## 🐛 Troubleshooting

### Agent Fails to Start
- Check agent config file syntax
- Verify task file exists and is readable
- Check session directory permissions

### Missing Results
- Check agent execution logs in result file
- Verify source code paths are correct
- Ensure required tools (Glob, Read, Grep) are available

### Low Confidence Scores
- Review validation criteria in task file
- Check if code structure matches expected patterns
- May indicate genuine documentation issues

### Conflicts Not Resolved
- Verify expert priority rules in coordinator
- Check confidence scores in result files
- Review conflict resolution logs in final report

## 📈 Performance

Typical execution time for a 4,000-line business logic document:

| Phase | Time | Notes |
|-------|------|-------|
| Document Analysis | 1-2 min | Parsing, extraction |
| Task Generation | 30 sec | 8 task files |
| Parallel Validation | 8-12 min | 8 agents running simultaneously |
| Result Aggregation | 1-2 min | Conflict resolution |
| **Total** | **10-16 min** | End-to-end |

## 🔒 Best Practices

1. **Version Control**: Commit validation reports to track documentation quality over time
2. **CI Integration**: Run validation on doc changes (future enhancement)
3. **Regular Runs**: Validate after major code refactoring
4. **Human Review**: Always review items flagged with low confidence
5. **Incremental Fixes**: Address high-priority (P0) issues first

## 📝 Maintenance

### Regular Tasks
- Archive old sessions from `workspace/` to `history/` (automatic)
- Review and update agent configurations based on new patterns
- Update templates if report format needs changes

### Version History
- v1.1 (2026-02-06): Added ER Diagram Validator (10 agents total), optimized output format
- v1.0 (2026-02-06): Initial release with 9 agents

## 🤝 Contributing

To improve this system:
1. Identify validation gaps or false positives
2. Propose new validation dimensions
3. Enhance confidence scoring algorithms
4. Improve conflict resolution strategies

## 📞 Support

For issues or questions:
- Check agent execution logs in result files
- Review FINAL_REPORT.md for detailed error messages
- Examine task files to verify input format

---

**System Version**: 1.1  
**Last Updated**: 2026-02-06  
**Total Agents**: 10 (1 coordinator + 9 expert validators)
