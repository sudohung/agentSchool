package ai.openclaw.ocjbot.skill;

import ai.openclaw.ocjbot.harness.Harness;

public record SkillContext(
    Harness harness,
    String sessionId,
    String userId
) {}