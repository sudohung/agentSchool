package ai.openclaw.ocjbot.skill;

import java.util.List;
import java.util.Map;

public interface Skill {
    
    String getId();
    
    String getName();
    
    String getDescription();
    
    String getCategory();
    
    SkillResult execute(SkillContext context, SkillInput input);
    
    default List<String> getRequiredTools() {
        return List.of();
    }
    
    default Map<String, Object> getDefaultConfig() {
        return Map.of();
    }
}