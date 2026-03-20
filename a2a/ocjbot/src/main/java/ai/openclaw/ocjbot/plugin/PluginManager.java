package ai.openclaw.ocjbot.plugin;

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