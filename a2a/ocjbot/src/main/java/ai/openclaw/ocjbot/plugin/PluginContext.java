package ai.openclaw.ocjbot.plugin;

import ai.openclaw.ocjbot.config.OcjbotProperties;
import ai.openclaw.ocjbot.event.EventBus;
import ai.openclaw.ocjbot.harness.Harness;

public record PluginContext(
    Harness harness,
    OcjbotProperties properties,
    EventBus eventBus,
    String pluginId
) {}