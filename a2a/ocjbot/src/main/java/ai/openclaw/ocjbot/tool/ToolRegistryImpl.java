package ai.openclaw.ocjbot.tool;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class ToolRegistryImpl implements ToolRegistry {
    
    private final Map<String, Tool> tools = new ConcurrentHashMap<>();
    
    @Override
    public void register(Tool tool) {
        tools.put(tool.getName(), tool);
    }
    
    @Override
    public void unregister(String name) {
        tools.remove(name);
    }
    
    @Override
    public Tool get(String name) {
        return tools.get(name);
    }
    
    @Override
    public List<Tool> getAll() {
        return List.copyOf(tools.values());
    }
    
    @Override
    public boolean exists(String name) {
        return tools.containsKey(name);
    }
}