package ai.openclaw.ocjbot.gateway.config;

import jakarta.annotation.PreDestroy;
import ai.openclaw.ocjbot.harness.Harness;
import ai.openclaw.ocjbot.harness.HarnessImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ShutdownConfig {

    private static final Logger log = LoggerFactory.getLogger(ShutdownConfig.class);

    private final Harness harness;

    public ShutdownConfig(Harness harness) {
        this.harness = harness;
    }

    @PreDestroy
    public void onShutdown() {
        log.info("Application shutting down...");
        if (harness instanceof HarnessImpl impl) {
            impl.shutdown();
        }
    }
}