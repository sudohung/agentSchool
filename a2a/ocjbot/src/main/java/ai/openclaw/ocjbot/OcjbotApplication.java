package ai.openclaw.ocjbot;

import ai.openclaw.ocjbot.config.OcjbotConfig;
import ai.openclaw.ocjbot.gateway.GatewayServer;
import ai.openclaw.ocjbot.harness.Harness;
import ai.openclaw.ocjbot.harness.HarnessImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OcjbotApplication {
    private static final Logger log = LoggerFactory.getLogger(OcjbotApplication.class);

    public static void main(String[] args) {
        log.info("╔════════════════════════════════════════════════════════════╗");
        log.info("║           OCJBot - Agent OS v2.1.0                         ║");
        log.info("║     OpenClaw Java Bot - Harness + Runtime Architecture      ║");
        log.info("╚════════════════════════════════════════════════════════════╝");
        
        try {
            Harness harness = new HarnessImpl();
            harness.initialize();
            
            OcjbotConfig config = harness.getConfig();
            
            GatewayServer gateway = new GatewayServer(harness, config);
            gateway.start();
            
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                log.info("Shutting down OCJBot...");
                gateway.stop();
                harness.shutdown();
                log.info("OCJBot stopped.");
            }));
            
            log.info("");
            log.info("┌─────────────────────────────────────────────────────────────┐");
            log.info("│  Gateway Started Successfully                               │");
            log.info("├─────────────────────────────────────────────────────────────┤");
            log.info("│  Web UI:      http://{}:{}                          │", 
                config.getGateway().getHost(), config.getGateway().getPort());
            log.info("│  WebSocket:   ws://{}:{}/ws                       │", 
                config.getGateway().getHost(), config.getGateway().getPort());
            log.info("│  Health API:  http://{}:{}/api/health               │", 
                config.getGateway().getHost(), config.getGateway().getPort());
            log.info("└─────────────────────────────────────────────────────────────┘");
            log.info("");
            
            Thread.currentThread().join();
            
        } catch (Exception e) {
            log.error("Failed to start OCJBot", e);
            System.exit(1);
        }
    }
}