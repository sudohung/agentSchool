package ai.openclaw.ocjbot.skill;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

public class SkillRegistryImpl implements SkillRegistry {
    
    private final Map<String, Skill> skills = new ConcurrentHashMap<>();
    
    @Override
    public void register(Skill skill) {
        skills.put(skill.getId(), skill);
    }
    
    @Override
    public void unregister(String skillId) {
        skills.remove(skillId);
    }
    
    @Override
    public Skill get(String skillId) {
        return skills.get(skillId);
    }
    
    @Override
    public List<Skill> getAll() {
        return new ArrayList<>(skills.values());
    }
    
    @Override
    public List<Skill> getByCategory(String category) {
        return skills.values().stream()
            .filter(s -> category.equals(s.getCategory()))
            .collect(Collectors.toList());
    }
}