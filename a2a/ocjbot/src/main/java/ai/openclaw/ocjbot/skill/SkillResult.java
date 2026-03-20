package ai.openclaw.ocjbot.skill;

public record SkillResult(
    boolean success,
    String output,
    String error
) {
    public static SkillResult success(String output) {
        return new SkillResult(true, output, null);
    }
    
    public static SkillResult failure(String error) {
        return new SkillResult(false, null, error);
    }
}