package ai.opencode.sdk;

/**
 * Resource not found exception.
 */
public class NotFoundException extends OpenCodeException {
    public NotFoundException(String message) {
        super(message);
    }
}
