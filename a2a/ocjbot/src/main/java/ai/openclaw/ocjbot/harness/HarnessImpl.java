package ai.openclaw.ocjbot.harness;

import ai.openclaw.ocjbot.config.ConfigLoader;
import ai.openclaw.ocjbot.config.OcjbotConfig;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.event.EventBusImpl;
import ai.openclaw.ocjbot.harness.loop.ReActLoop;
import ai.openclaw.ocjbot.plugin.PluginManager;
import ai.openclaw.ocjbot.plugin.PluginManagerImpl;
import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.mock.MockRuntime;
import ai.openclaw.ocjbot.skill.SkillRegistry;
import ai.openclaw.ocjbot.skill.SkillRegistryImpl;
import ai.openclaw.ocjbot.tool.ToolRegistry;
import ai.openclaw.ocjbot.tool.ToolRegistryImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class HarnessImpl implements Harness {
    private static final Logger log = LoggerFactory.getLogger(HarnessImpl.class);
    
    private final Map<Class<?>, Object> services = new ConcurrentHashMap<>();
    
    private OcjbotConfig config;
    private AgentRuntime runtime;
    private AgentLoop agentLoop;
    private PluginManager pluginManager;
    private EventBus eventBus;
    private ToolRegistry toolRegistry;
    private SkillRegistry skillRegistry;
    
    @Override
    public void initialize() {
        log.info("╔════════════════════════════════════════════════════════════╗");
        log.info("║              Initializing Harness...                        ║");
        log.info("╚════════════════════════════════════════════════════════════╝");
        
        config = ConfigLoader.load();
        services.put(OcjbotConfig.class, config);
        
        eventBus = new EventBusImpl();
        services.put(EventBus.class, eventBus);
        
        toolRegistry = new ToolRegistryImpl();
        services.put(ToolRegistry.class, toolRegistry);
        
        skillRegistry = new SkillRegistryImpl();
        services.put(SkillRegistry.class, skillRegistry);
        
        runtime = new MockRuntime();
        runtime.initialize();
        services.put(AgentRuntime.class, runtime);
        
        agentLoop = new ReActLoop(this);
        
        pluginManager = new PluginManagerImpl(this);
        services.put(PluginManager.class, pluginManager);
        
        log.info("┌─────────────────────────────────────────────────────────────┐");
        log.info("│  Harness Initialized Successfully                           │");
        log.info("├─────────────────────────────────────────────────────────────┤");
        log.info("│  Runtime:     {}", String.format("%-40s", runtime.getName()) + "│");
        log.info("│  Type:        {}", String.format("%-40s", runtime.getType()) + "│");
        log.info("│  Agent Loop:  {}", String.format("%-40s", agentLoop.getName()) + "│");
        log.info("│  Max Iter:    {}", String.format("%-40s", agentLoop.getMaxIterations()) + "│");
        log.info("└─────────────────────────────────────────────────────────────┘");
    }
    
    @Override
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
    public OcjbotConfig getConfig() {
        return config;
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
}