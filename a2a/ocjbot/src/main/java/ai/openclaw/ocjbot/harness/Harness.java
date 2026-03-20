package ai.openclaw.ocjbot.harness;

import ai.openclaw.ocjbot.config.OcjbotProperties;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.plugin.PluginManager;
import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.skill.SkillRegistry;
import ai.openclaw.ocjbot.tool.ToolRegistry;

public interface Harness {
    
    OcjbotProperties getProperties();
    
    AgentRuntime getRuntime();
    
    AgentLoop getAgentLoop();
    
    PluginManager getPluginManager();
    
    EventBus getEventBus();
    
    ToolRegistry getToolRegistry();
    
    SkillRegistry getSkillRegistry();
    
    <T> T getService(Class<T> serviceClass);
    
    void registerService(Class<?> serviceClass, Object service);
}