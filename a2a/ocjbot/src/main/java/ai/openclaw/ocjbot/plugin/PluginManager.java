package ai.openclaw.ocjbot.plugin;

import ai.openclaw.ocjbot.config.OcjbotProperties;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.tool.ToolRegistry;
import ai.openclaw.ocjbot.skill.SkillRegistry;

import java.util.List;

public interface PluginManager {
    
    void loadPlugins();
    
    void unloadPlugins();
    
    void loadPlugin(String pluginPath);
    
    void unloadPlugin(String pluginId);
    
    Plugin getPlugin(String pluginId);
    
    boolean isPluginLoaded(String pluginId);
    
    List<Plugin> getAllPlugins();
}