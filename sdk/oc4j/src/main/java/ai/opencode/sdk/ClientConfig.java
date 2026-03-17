package ai.opencode.sdk;

import lombok.Builder;
import lombok.Getter;
import java.time.Duration;

@Getter
@Builder
public class ClientConfig {
    private final String baseUrl;
    private final String username;
    private final String password;
    private final Duration timeout;
    private final String directory;
    private final String workspace;

    public static class ClientConfigBuilder {
        private String baseUrl = "http://127.0.0.1:4096";
        private String username;
        private String password;
        private Duration timeout = Duration.ofSeconds(30);
        private String directory;
        private String workspace;

        public ClientConfigBuilder password(String password) {
            this.password = password;
            if (password != null && username == null) {
                this.username = "opencode";
            }
            return this;
        }
    }
}
