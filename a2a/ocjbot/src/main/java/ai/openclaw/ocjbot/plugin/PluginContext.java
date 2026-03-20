package ai.openclaw.ocjbot.plugin;

import ai.openclaw.ocjbot.config.OcjbotConfig;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.harness.Harness;

public record PluginContext(
    Harness harness,
    OcjbotConfig config,
    EventBus eventBus,
    String pluginId
) {}