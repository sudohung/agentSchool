package ai.openclaw.ocjbot.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public final class ConfigLoader {
    private static final Logger log = LoggerFactory.getLogger(ConfigLoader.class);
    private static final ObjectMapper YAML_MAPPER = new ObjectMapper(new YAMLFactory());
    private static final ObjectMapper JSON_MAPPER = new ObjectMapper();
    
    private static final String[] CONFIG_PATHS = {
        "ocjbot.yaml",
        "ocjbot.yml",
        "ocjbot.json",
        ".ocjbot/config.yaml",
        ".ocjbot/config.yml",
        ".ocjbot/config.json"
    };
    
    private ConfigLoader() {}
    
    public static OcjbotConfig load() {
        return load(null);
    }
    
    public static OcjbotConfig load(String configPath) {
        OcjbotConfig config = new OcjbotConfig();
        
        Path path = findConfigFile(configPath);
        if (path != null) {
            try {
                log.info("Loading configuration from: {}", path);
                ObjectMapper mapper = path.toString().endsWith(".json") ? JSON_MAPPER : YAML_MAPPER;
                config = mapper.readValue(path.toFile(), OcjbotConfig.class);
            } catch (Exception e) {
                log.warn("Failed to load config from {}, using defaults", path, e);
            }
        } else {
            log.info("No configuration file found, using defaults");
        }
        
        overrideFromEnv(config);
        
        return config;
    }
    
    private static Path findConfigFile(String configPath) {
        if (configPath != null) {
            Path path = Paths.get(configPath);
            if (Files.exists(path)) {
                return path;
            }
        }
        
        for (String p : CONFIG_PATHS) {
            Path path = Paths.get(p);
            if (Files.exists(path)) {
                return path;
            }
        }
        
        return null;
    }
    
    private static void overrideFromEnv(OcjbotConfig config) {
        String openaiKey = System.getenv("OPENAI_API_KEY");
        if (openaiKey != null) {
            config.getLlm().getProviders().computeIfAbsent("openai", 
                k -> new OcjbotConfig.LlmProviderConfig("gpt-4o", null))
                .setApiKey(openaiKey);
        }
        
        String anthropicKey = System.getenv("ANTHROPIC_API_KEY");
        if (anthropicKey != null) {
            config.getLlm().getProviders().computeIfAbsent("anthropic", 
                k -> new OcjbotConfig.LlmProviderConfig("claude-3-5-sonnet-20241022", null))
                .setApiKey(anthropicKey);
        }
        
        String gatewayPort = System.getenv("OCJBOT_GATEWAY_PORT");
        if (gatewayPort != null) {
            config.getGateway().setPort(Integer.parseInt(gatewayPort));
        }
    }
}