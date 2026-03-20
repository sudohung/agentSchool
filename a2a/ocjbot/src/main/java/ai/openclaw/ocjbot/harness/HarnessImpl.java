package ai.openclaw.ocjbot.harness;

import ai.openclaw.ocjbot.config.OcjbotProperties;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.plugin.PluginManager;
import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.skill.SkillRegistry;
import ai.openclaw.ocjbot.tool.ToolRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class HarnessImpl implements Harness {
    
    private static final Logger log = LoggerFactory.getLogger(HarnessImpl.class);
    
    private final Map<Class<?>, Object> services = new ConcurrentHashMap<>();
    
    private OcjbotProperties properties;
    private AgentRuntime runtime;
    private AgentLoop agentLoop;
    private PluginManager pluginManager;
    private EventBus eventBus;
    private ToolRegistry toolRegistry;
    private SkillRegistry skillRegistry;
    
    public void initialize() {
        log.info("╔════════════════════════════════════════════════════════════╗");
        log.info("║              Initializing Harness...                        ║");
        log.info("╚════════════════════════════════════════════════════════════╝");
        
        services.put(OcjbotProperties.class, properties);
        services.put(AgentRuntime.class, runtime);
        services.put(EventBus.class, eventBus);
        services.put(ToolRegistry.class, toolRegistry);
        services.put(SkillRegistry.class, skillRegistry);
        services.put(AgentLoop.class, agentLoop);
        services.put(PluginManager.class, pluginManager);
        
        runtime.initialize();
        
        log.info("┌─────────────────────────────────────────────────────────────┐");
        log.info("│  Harness Initialized Successfully                           │");
        log.info("├─────────────────────────────────────────────────────────────┤");
        log.info("│  Runtime:     {}", String.format("%-40s", runtime.getName()) + "│");
        log.info("│  Type:        {}", String.format("%-40s", runtime.getType()) + "│");
        log.info("│  Agent Loop:  {}", String.format("%-40s", agentLoop.getName()) + "│");
        log.info("│  Max Iter:    {}", String.format("%-40s", agentLoop.getMaxIterations()) + "│");
        log.info("└─────────────────────────────────────────────────────────────┘");
    }
    
    public void shutdown() {
        log.info("Shutting down Harness...");
        
        if (runtime != null) {
            try {
                runtime.close();
            } catch (Exception e) {
                log.error("Failed to close runtime", e);
            }
        }
        
        services.clear();
        log.info("Harness shutdown complete.");
    }

    @Override
    public OcjbotProperties getProperties() {
        return properties;
    }

    @Override
    public AgentRuntime getRuntime() {
        return runtime;
    }

    @Override
    public AgentLoop getAgentLoop() {
        return agentLoop;
    }

    @Override
    public PluginManager getPluginManager() {
        return pluginManager;
    }

    @Override
    public EventBus getEventBus() {
        return eventBus;
    }

    @Override
    public ToolRegistry getToolRegistry() {
        return toolRegistry;
    }

    @Override
    public SkillRegistry getSkillRegistry() {
        return skillRegistry;
    }

    @Override
    @SuppressWarnings("unchecked")
    public <T> T getService(Class<T> serviceClass) {
        return (T) services.get(serviceClass);
    }

    @Override
    public void registerService(Class<?> serviceClass, Object service) {
        services.put(serviceClass, service);
    }

    public void setProperties(OcjbotProperties properties) {
        this.properties = properties;
    }

    public void setRuntime(AgentRuntime runtime) {
        this.runtime = runtime;
    }

    public void setAgentLoop(AgentLoop agentLoop) {
        this.agentLoop = agentLoop;
    }

    public void setPluginManager(PluginManager pluginManager) {
        this.pluginManager = pluginManager;
    }

    public void setEventBus(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    public void setToolRegistry(ToolRegistry toolRegistry) {
        this.toolRegistry = toolRegistry;
    }

    public void setSkillRegistry(SkillRegistry skillRegistry) {
        this.skillRegistry = skillRegistry;
    }
}