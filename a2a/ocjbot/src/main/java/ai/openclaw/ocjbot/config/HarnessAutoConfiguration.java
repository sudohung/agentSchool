package ai.openclaw.ocjbot.config;

import ai.openclaw.ocjbot.harness.*;
import ai.openclaw.ocjbot.harness.loop.ReActLoop;
import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.mock.MockRuntime;
import ai.openclaw.ocjbot.runtime.opencode.OpenCodeRuntime;
import ai.openclaw.ocjbot.runtime.opencode.OpenCodeRuntimeConfig;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.event.EventBusImpl;
import ai.openclaw.ocjbot.tool.ToolRegistry;
import ai.openclaw.ocjbot.tool.ToolRegistryImpl;
import ai.openclaw.ocjbot.skill.SkillRegistry;
import ai.openclaw.ocjbot.skill.SkillRegistryImpl;
import ai.openclaw.ocjbot.plugin.PluginManager;
import ai.openclaw.ocjbot.plugin.PluginManagerImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

@Configuration
public class HarnessAutoConfiguration {

    private static final Logger log = LoggerFactory.getLogger(HarnessAutoConfiguration.class);

    @Bean
    @ConditionalOnMissingBean
    public EventBus eventBus() {
        return new EventBusImpl();
    }

    @Bean
    @ConditionalOnMissingBean
    public ToolRegistry toolRegistry() {
        return new ToolRegistryImpl();
    }

    @Bean
    @ConditionalOnMissingBean
    public SkillRegistry skillRegistry() {
        return new SkillRegistryImpl();
    }

    @Bean
    @ConditionalOnMissingBean
    public AgentRuntime agentRuntime(OcjbotProperties properties) {
        String runtimeType = properties.getRuntime().getType();
        
        log.info("Creating AgentRuntime of type: {}", runtimeType);
        
        return switch (runtimeType.toLowerCase()) {
            case "opencode" -> createOpenCodeRuntime(properties);
            case "mock" -> createMockRuntime();
            default -> {
                log.warn("Unknown runtime type: {}, using mock", runtimeType);
                yield createMockRuntime();
            }
        };
    }

    private AgentRuntime createOpenCodeRuntime(OcjbotProperties properties) {
        OcjbotProperties.RuntimeConfig runtimeConfig = properties.getRuntime();
        
        OpenCodeRuntimeConfig config = OpenCodeRuntimeConfig.builder()
            .baseUrl(runtimeConfig.getOpenCodeBaseUrl())
            .username(runtimeConfig.getOpenCodeUsername())
            .password(runtimeConfig.getOpenCodePassword())
            .directory(runtimeConfig.getOpenCodeDirectory())
            .workspace(runtimeConfig.getOpenCodeWorkspace())
            .timeout(runtimeConfig.getOpenCodeTimeout() != null 
                ? Duration.ofMillis(runtimeConfig.getOpenCodeTimeout()) 
                : Duration.ofSeconds(60))
            .defaultProvider(runtimeConfig.getDefaultProvider())
            .defaultModel(runtimeConfig.getDefaultModel())
            .build();
        
        return new OpenCodeRuntime(config);
    }

    private AgentRuntime createMockRuntime() {
        return new MockRuntime();
    }

    @Bean
    @ConditionalOnMissingBean
    public PluginManager pluginManager(
            OcjbotProperties properties,
            EventBus eventBus,
            ToolRegistry toolRegistry,
            SkillRegistry skillRegistry) {
        return new PluginManagerImpl(properties, eventBus, toolRegistry, skillRegistry);
    }

    @Bean
    @ConditionalOnMissingBean
    public Harness harness(
            OcjbotProperties properties,
            AgentRuntime runtime,
            EventBus eventBus,
            ToolRegistry toolRegistry,
            SkillRegistry skillRegistry,
            PluginManager pluginManager) {
        
        HarnessImpl harness = new HarnessImpl();
        harness.setProperties(properties);
        harness.setRuntime(runtime);
        harness.setEventBus(eventBus);
        harness.setToolRegistry(toolRegistry);
        harness.setSkillRegistry(skillRegistry);
        harness.setPluginManager(pluginManager);
        
        AgentLoop agentLoop = new ReActLoop(harness, 10);
        harness.setAgentLoop(agentLoop);
        
        harness.initialize();
        
        return harness;
    }
}