package ai.openclaw.ocjbot.config;

import lombok.Data;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Data
public class OcjbotConfig {
    private AgentConfig agent = new AgentConfig();
    private GatewayConfig gateway = new GatewayConfig();
    private MemoryConfig memory = new MemoryConfig();
    private LlmConfig llm = new LlmConfig();
    private List<String> tools = new ArrayList<>();
    private List<SkillConfig> skills = new ArrayList<>();
    
    @Data
    public static class AgentConfig {
        private String name = "OCJBot Assistant";
        private String model = "openai/gpt-4o";
        private String description = "A comprehensive AI personal assistant";
    }
    
    @Data
    public static class GatewayConfig {
        private String host = "127.0.0.1";
        private int port = 18789;
        private int restPort = 8080;
        private boolean websocketEnabled = true;
        private boolean restEnabled = true;
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
        
        public LlmConfig() {
            providers.put("openai", new LlmProviderConfig("gpt-4o", null));
            providers.put("anthropic", new LlmProviderConfig("claude-3-5-sonnet-20241022", null));
        }
    }
    
    @Data
    public static class LlmProviderConfig {
        private String model;
        private String apiKey;
        private String baseUrl;
        
        public LlmProviderConfig(String model, String apiKey) {
            this.model = model;
            this.apiKey = apiKey;
        }
    }
    
    @Data
    public static class SkillConfig {
        private String id;
        private boolean enabled = true;
        private Map<String, Object> config = new HashMap<>();
    }
}