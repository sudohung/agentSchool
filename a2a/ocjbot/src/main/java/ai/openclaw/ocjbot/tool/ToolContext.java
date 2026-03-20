package ai.openclaw.ocjbot.tool;

import ai.openclaw.ocjbot.harness.Harness;

public record ToolContext(
    Harness harness,
    String sessionId,
    String userId
) {}