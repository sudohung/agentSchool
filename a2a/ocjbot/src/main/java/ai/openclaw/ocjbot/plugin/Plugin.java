package ai.openclaw.ocjbot.plugin;

import ai.openclaw.ocjbot.event.EventHandler;
import ai.openclaw.ocjbot.skill.Skill;
import ai.openclaw.ocjbot.tool.Tool;

import java.util.List;

public interface Plugin {
    
    String getId();
    
    String getName();
    
    String getVersion();
    
    void initialize(PluginContext context);
    
    void start();
    
    void stop();
    
    void destroy();
    
    default List<Tool> getTools() {
        return List.of();
    }
    
    default List<EventHandler<?>> getEventHandlers() {
        return List.of();
    }
    
    default List<Skill> getSkills() {
        return List.of();
    }
}