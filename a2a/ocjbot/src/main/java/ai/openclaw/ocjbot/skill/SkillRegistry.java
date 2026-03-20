package ai.openclaw.ocjbot.skill;

import java.util.List;

public interface SkillRegistry {
    
    void register(Skill skill);
    
    void unregister(String skillId);
    
    Skill get(String skillId);
    
    List<Skill> getAll();
    
    List<Skill> getByCategory(String category);
}