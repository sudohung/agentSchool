package ai.opencode.sdk;

/**
 * Base exception for OpenCode SDK.
 */
public class OpenCodeException extends RuntimeException {
    public OpenCodeException(String message) {
        super(message);
    }
    
    public OpenCodeException(String message, Throwable cause) {
        super(message, cause);
    }
}
