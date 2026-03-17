package ai.opencode.sdk;

/**
 * Connection exception.
 */
public class ConnectionException extends OpenCodeException {
    public ConnectionException(String message) {
        super(message);
    }
    
    public ConnectionException(String message, Throwable cause) {
        super(message, cause);
    }
}
