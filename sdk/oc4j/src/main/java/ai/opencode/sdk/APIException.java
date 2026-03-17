package ai.opencode.sdk;

import lombok.Getter;
import java.util.Map;

/**
 * API error with status code.
 */
@Getter
public class APIException extends OpenCodeException {
    private final int statusCode;
    private final String responseBody;
    private final Map<String, String> headers;
    private final boolean retryable;

    public APIException(int statusCode, String message, String responseBody, 
                       Map<String, String> headers, boolean retryable) {
        super(message);
        this.statusCode = statusCode;
        this.responseBody = responseBody;
        this.headers = headers;
        this.retryable = retryable;
    }
}
