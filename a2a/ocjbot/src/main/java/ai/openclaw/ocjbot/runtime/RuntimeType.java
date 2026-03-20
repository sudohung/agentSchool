package ai.openclaw.ocjbot.runtime;

/**
 * Runtime 类型枚举
 */
public enum RuntimeType {
    
    /**
     * 基于 OpenCode Server，使用 oc4j SDK
     */
    OPENCODE("opencode"),
    
    /**
     * 直接调用 LLM API (OpenAI, Anthropic, etc.)
     */
    DIRECT_LLM("direct-llm"),
    
    /**
     * 基于 LangChain4j
     */
    LANGCHAIN("langchain"),
    
    /**
     * Mock 实现，用于测试
     */
    MOCK("mock");
    
    private final String code;
    
    RuntimeType(String code) {
        this.code = code;
    }
    
    public String getCode() {
        return code;
    }
    
    public static RuntimeType fromCode(String code) {
        for (RuntimeType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return OPENCODE;
    }
}