package ai.openclaw.ocjbot.skill;

import java.util.Map;

public record SkillInput(
    String query,
    Map<String, Object> parameters
) {
    public static SkillInput of(String query) {
        return new SkillInput(query, Map.of());
    }
    
    public static SkillInput of(String query, Map<String, Object> parameters) {
        return new SkillInput(query, parameters);
    }
}