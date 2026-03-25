package ai.openclaw.ocjbot.runtime.opencode;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Duration;

/**
 * OpenCode Runtime 配置
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OpenCodeRuntimeConfig {
    
    @Builder.Default
    private String baseUrl = "http://127.0.0.1:4096";
    
    private String username;
    private String password;
    private String directory;
    private String workspace;
    
    @Builder.Default
    private Duration timeout = Duration.ofSeconds(60);
    
    /** 默认 Provider ID */
    private String defaultProvider;
    
    /** 默认 Model ID */
    private String defaultModel;
    
    public static OpenCodeRuntimeConfig defaults() {
        return OpenCodeRuntimeConfig.builder().build();
    }
    
    public static OpenCodeRuntimeConfig of(String baseUrl, String username, String password) {
        return OpenCodeRuntimeConfig.builder()
            .baseUrl(baseUrl)
            .username(username)
            .password(password)
            .build();
    }
}