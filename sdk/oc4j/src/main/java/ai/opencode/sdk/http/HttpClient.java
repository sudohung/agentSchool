package ai.opencode.sdk.http;

import ai.opencode.sdk.APIException;
import ai.opencode.sdk.ConnectionException;
import ai.opencode.sdk.ClientConfig;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;

/**
 * Synchronous HTTP client for OpenCode API.
 */
public class HttpClient {
    private final OkHttpClient client;
    private final ObjectMapper mapper;
    private final String baseUrl;
    private final String directory;
    private final String workspace;
    private final Request.Builder requestBuilder;

    public HttpClient(ClientConfig config) {
        this.mapper = new ObjectMapper();
        this.baseUrl = config.getBaseUrl();
        this.directory = config.getDirectory();
        this.workspace = config.getWorkspace();

        this.client = new OkHttpClient.Builder()
            .connectTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .readTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .writeTimeout(config.getTimeout().getSeconds(), TimeUnit.SECONDS)
            .build();

        this.requestBuilder = new Request.Builder();

        if (config.getUsername() != null && config.getPassword() != null) {
            String credentials = Credentials.basic(config.getUsername(), config.getPassword());
            requestBuilder.addHeader("Authorization", credentials);
        }
    }

    public <T> T get(String path, Class<T> responseType) {
        return execute(buildRequest("GET", path, null), responseType);
    }

    public <T> T get(String path, Map<String, ?> params, Class<T> responseType) {
        return execute(buildRequestWithParams("GET", path, null, params), responseType);
    }

    public <T> T post(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("POST", path, body), responseType);
    }

    public <T> T put(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PUT", path, body), responseType);
    }

    public <T> T patch(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PATCH", path, body), responseType);
    }

    public void delete(String path) {
        execute(buildRequest("DELETE", path, null), Void.class);
    }

    public Boolean deleteWithResponse(String path) {
        return execute(buildRequest("DELETE", path, null), Boolean.class);
    }

    private <T> T execute(Request request, Class<T> responseType) {
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                String body = response.body() != null ? response.body().string() : "";
                Map<String, String> headers = new HashMap<>();
                response.headers().forEach(h -> headers.put(h.getName(), h.getValue()));
                boolean retryable = response.code() >= 500 || response.code() == 429;
                throw new APIException(response.code(),
                    "HTTP " + response.code() + ": " + response.message(),
                    body, headers, retryable);
            }

            ResponseBody responseBody = response.body();
            if (responseBody == null) {
                return null;
            }

            String json = responseBody.string();
            if (responseType == Void.class) {
                return null;
            }
            if (responseType == Boolean.class) {
                if ("true".equals(json) || "false".equals(json)) {
                    return responseType.cast(Boolean.parseBoolean(json));
                }
                return null;
            }
            return mapper.readValue(json, responseType);
        } catch (IOException e) {
            throw new ConnectionException("Request failed: " + e.getMessage());
        }
    }

    private Request buildRequest(String method, String path, Object body) {
        return buildRequestWithParams(method, path, body, null);
    }

    private Request buildRequestWithParams(String method, String path, Object body, Map<String, ?> extraParams) {
        HttpUrl.Builder urlBuilder = HttpUrl.parse(baseUrl + path).newBuilder();

        if (directory != null) {
            urlBuilder.addQueryParameter("directory", directory);
        }
        if (workspace != null) {
            urlBuilder.addQueryParameter("workspace", workspace);
        }
        if (extraParams != null) {
            extraParams.forEach((key, value) -> {
                if (value != null) {
                    urlBuilder.addQueryParameter(key, value.toString());
                }
            });
        }

        Request.Builder builder = requestBuilder.newBuilder()
            .url(urlBuilder.build());

        if (body != null) {
            builder.method(method, RequestBody.create(
                toJson(body),
                MediaType.parse("application/json; charset=utf-8")
            ));
        } else {
            builder.method(method, null);
        }

        return builder.build();
    }

    private String toJson(Object obj) {
        try {
            return mapper.writeValueAsString(obj);
        } catch (Exception e) {
            throw new ConnectionException("Failed to serialize object: " + e.getMessage());
        }
    }

    public <T> Iterator<T> streamSse(String path, Function<String, T> parser) {
        Request request = buildRequest("GET", path, null);
        try {
            Response response = client.newCall(request).execute();
            if (!response.isSuccessful()) {
                String body = response.body() != null ? response.body().string() : "";
                response.close();
                Map<String, String> headers = new HashMap<>();
                response.headers().forEach(h -> headers.put(h.getName(), h.getValue()));
                boolean retryable = response.code() >= 500 || response.code() == 429;
                throw new APIException(response.code(),
                    "HTTP " + response.code() + ": " + response.message(),
                    body, headers, retryable);
            }
            ResponseBody responseBody = response.body();
            if (responseBody == null) {
                response.close();
                throw new ConnectionException("Empty response body");
            }
            InputStream inputStream = responseBody.byteStream();
            return new SseIterator<>(inputStream, parser);
        } catch (IOException e) {
            throw new ConnectionException("Failed to open SSE stream: " + e.getMessage());
        }
    }

    public <T> Iterator<T> streamSse(String path, Map<String, String> params, Function<String, T> parser) {
        Request request = buildRequest("GET", path, null, params);
        try {
            Response response = client.newCall(request).execute();
            if (!response.isSuccessful()) {
                String body = response.body() != null ? response.body().string() : "";
                response.close();
                Map<String, String> headers = new HashMap<>();
                response.headers().forEach(h -> headers.put(h.getName(), h.getValue()));
                boolean retryable = response.code() >= 500 || response.code() == 429;
                throw new APIException(response.code(),
                    "HTTP " + response.code() + ": " + response.message(),
                    body, headers, retryable);
            }
            ResponseBody responseBody = response.body();
            if (responseBody == null) {
                response.close();
                throw new ConnectionException("Empty response body");
            }
            InputStream inputStream = responseBody.byteStream();
            return new SseIterator<>(inputStream, parser);
        } catch (IOException e) {
            throw new ConnectionException("Failed to open SSE stream: " + e.getMessage());
        }
    }

    private Request buildRequest(String method, String path, Object body, Map<String, String> extraParams) {
        HttpUrl.Builder urlBuilder = HttpUrl.parse(baseUrl + path).newBuilder();

        if (directory != null) {
            urlBuilder.addQueryParameter("directory", directory);
        }
        if (workspace != null) {
            urlBuilder.addQueryParameter("workspace", workspace);
        }
        if (extraParams != null) {
            extraParams.forEach((key, value) -> {
                if (value != null) {
                    urlBuilder.addQueryParameter(key, value);
                }
            });
        }

        Request.Builder builder = requestBuilder.newBuilder()
            .url(urlBuilder.build());

        if (body != null) {
            builder.method(method, RequestBody.create(
                toJson(body),
                MediaType.parse("application/json; charset=utf-8")
            ));
        } else {
            builder.method(method, null);
        }

        return builder.build();
    }
}
