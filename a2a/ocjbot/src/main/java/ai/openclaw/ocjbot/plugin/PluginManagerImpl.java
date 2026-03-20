package ai.openclaw.ocjbot.plugin;

import ai.openclaw.ocjbot.config.OcjbotProperties;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.tool.ToolRegistry;
import ai.openclaw.ocjbot.skill.SkillRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class PluginManagerImpl implements PluginManager {
    
    private static final Logger log = LoggerFactory.getLogger(PluginManagerImpl.class);
    
    private final OcjbotProperties properties;
    private final EventBus eventBus;
    private final ToolRegistry toolRegistry;
    private final SkillRegistry skillRegistry;
    
    private final Map<String, Plugin> plugins = new ConcurrentHashMap<>();
    
    public PluginManagerImpl(
            OcjbotProperties properties,
            EventBus eventBus,
            ToolRegistry toolRegistry,
            SkillRegistry skillRegistry) {
        this.properties = properties;
        this.eventBus = eventBus;
        this.toolRegistry = toolRegistry;
        this.skillRegistry = skillRegistry;
    }
    
    @Override
    public void loadPlugins() {
        log.info("Loading plugins...");
        log.info("No plugins to load.");
    }
    
    @Override
    public void unloadPlugins() {
        log.info("Unloading plugins...");
        for (Plugin plugin : plugins.values()) {
            try {
                plugin.stop();
                plugin.destroy();
            } catch (Exception e) {
                log.error("Failed to unload plugin: {}", plugin.getId(), e);
            }
        }
        plugins.clear();
    }
    
    @Override
    public void loadPlugin(String pluginPath) {
        log.info("Loading plugin from: {}", pluginPath);
    }
    
    @Override
    public void unloadPlugin(String pluginId) {
        Plugin plugin = plugins.remove(pluginId);
        if (plugin != null) {
            plugin.stop();
            plugin.destroy();
            log.info("Plugin unloaded: {}", pluginId);
        }
    }
    
    @Override
    public Plugin getPlugin(String pluginId) {
        return plugins.get(pluginId);
    }
    
    @Override
    public boolean isPluginLoaded(String pluginId) {
        return plugins.containsKey(pluginId);
    }
    
    @Override
    public List<Plugin> getAllPlugins() {
        return new ArrayList<>(plugins.values());
    }
}