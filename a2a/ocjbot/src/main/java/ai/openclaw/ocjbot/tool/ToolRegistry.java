package ai.openclaw.ocjbot.tool;

import java.util.List;

public interface ToolRegistry {
    
    void register(Tool tool);
    
    void unregister(String name);
    
    Tool get(String name);
    
    List<Tool> getAll();
    
    boolean exists(String name);
}