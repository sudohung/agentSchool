package ai.openclaw.ocjbot.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Data
@Component
@Validated
@ConfigurationProperties(prefix = "ocjbot")
public class OcjbotProperties {

    private AgentConfig agent = new AgentConfig();
    private GatewayConfig gateway = new GatewayConfig();
    private MemoryConfig memory = new MemoryConfig();
    private LlmConfig llm = new LlmConfig();
    private RuntimeConfig runtime = new RuntimeConfig();
    private List<String> tools = new ArrayList<>();
    private List<SkillConfig> skills = new ArrayList<>();

    @Data
    public static class AgentConfig {
        @NotBlank
        private String name = "OCJBot Assistant";
        @NotBlank
        private String model = "openai/gpt-4o";
        private String description = "A comprehensive AI personal assistant";
        private double temperature = 0.7;
        private int maxTokens = 4096;
    }

    @Data
    public static class GatewayConfig {
        @NotBlank
        private String host = "127.0.0.1";
        @NotNull
        private Integer port = 18789;
        private boolean websocketEnabled = true;
        private boolean restEnabled = true;
        private String allowedOrigins = "*";
    }

    @Data
    public static class MemoryConfig {
        private boolean enabled = true;
        private boolean autoRecall = true;
        private boolean autoCapture = true;
        private int topK = 5;
        private double threshold = 0.5;
        private String storagePath = ".ocjbot/memory";
    }

    @Data
    public static class LlmConfig {
        private Map<String, LlmProviderConfig> providers = new HashMap<>();
    }

    @Data
    public static class LlmProviderConfig {
        private String model;
        private String apiKey;
        private String baseUrl;
    }

    @Data
    public static class RuntimeConfig {
        @NotBlank
        private String type = "mock";
        private String openCodeBaseUrl = "http://127.0.0.1:4096";
        private String openCodeUsername;
        private String openCodePassword;
        private String openCodeDirectory;
        private String openCodeWorkspace;
        private Long openCodeTimeout = 60000L;
        
        /** 默认 Provider ID */
        private String defaultProvider;
        
        /** 默认 Model ID */
        private String defaultModel;
    }

    @Data
    public static class SkillConfig {
        private String id;
        private boolean enabled = true;
        private Map<String, Object> config = new HashMap<>();
    }
}