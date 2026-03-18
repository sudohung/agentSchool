package ai.opencode.sdk.http;

import ai.opencode.sdk.APIException;
import ai.opencode.sdk.ConnectionException;
import ai.opencode.sdk.ClientConfig;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Flow;
import java.util.concurrent.SubmissionPublisher;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;

/**
 * Asynchronous HTTP client for OpenCode API.
 */
public class AsyncHttpClient {
    private final OkHttpClient client;
    private final ObjectMapper mapper;
    private final String baseUrl;
    private final String directory;
    private final String workspace;
    private final Request.Builder requestBuilder;

    public AsyncHttpClient(ClientConfig config) {
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

    public <T> CompletableFuture<T> get(String path, Class<T> responseType) {
        return execute(buildRequest("GET", path, null), responseType);
    }

    public <T> CompletableFuture<T> post(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("POST", path, body), responseType);
    }

    public <T> CompletableFuture<T> put(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PUT", path, body), responseType);
    }

    public <T> CompletableFuture<T> patch(String path, Object body, Class<T> responseType) {
        return execute(buildRequest("PATCH", path, body), responseType);
    }

    public CompletableFuture<Void> delete(String path) {
        return execute(buildRequest("DELETE", path, null), Void.class);
    }

    private <T> CompletableFuture<T> execute(Request request, Class<T> responseType) {
        CompletableFuture<T> future = new CompletableFuture<>();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                future.completeExceptionally(new ConnectionException("Request failed: " + e.getMessage()));
            }

            @Override
            public void onResponse(Call call, Response response) {
                try {
                    if (!response.isSuccessful()) {
                        String body = response.body() != null ? response.body().string() : "";
                        Map<String, String> headers = new HashMap<>();
                        response.headers().forEach(h -> headers.put(h.getName(), h.getValue()));
                        boolean retryable = response.code() >= 500 || response.code() == 429;
                        future.completeExceptionally(new APIException(
                            response.code(),
                            "HTTP " + response.code() + ": " + response.message(),
                            body, headers, retryable));
                        return;
                    }

                    ResponseBody responseBody = response.body();
                    if (responseBody == null) {
                        future.complete(null);
                        return;
                    }

                    String json = responseBody.string();
                    if (responseType == Void.class) {
                        future.complete(null);
                    } else if (responseType == Boolean.class) {
                        if ("true".equals(json) || "false".equals(json)) {
                            future.complete(responseType.cast(Boolean.parseBoolean(json)));
                        } else {
                            future.complete(null);
                        }
                    } else {
                        future.complete(mapper.readValue(json, responseType));
                    }
                } catch (IOException e) {
                    future.completeExceptionally(new ConnectionException("Response parsing failed: " + e.getMessage()));
                }
            }
        });

        return future;
    }

    private Request buildRequest(String method, String path, Object body) {
        HttpUrl.Builder urlBuilder = HttpUrl.parse(baseUrl + path).newBuilder();

        if (directory != null) {
            urlBuilder.addQueryParameter("directory", directory);
        }
        if (workspace != null) {
            urlBuilder.addQueryParameter("workspace", workspace);
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

    public <T> Flow.Publisher<T> streamSse(String path, Function<String, T> parser) {
        SubmissionPublisher<T> publisher = new SubmissionPublisher<>();
        Request request = buildRequest("GET", path, null);

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                publisher.closeExceptionally(new ConnectionException("SSE stream failed: " + e.getMessage()));
            }

            @Override
            public void onResponse(Call call, Response response) {
                try {
                    if (!response.isSuccessful()) {
                        String body = response.body() != null ? response.body().string() : "";
                        response.close();
                        Map<String, String> headers = new HashMap<>();
                        response.headers().forEach(h -> headers.put(h.getName(), h.getValue()));
                        boolean retryable = response.code() >= 500 || response.code() == 429;
                        publisher.closeExceptionally(new APIException(
                            response.code(),
                            "HTTP " + response.code() + ": " + response.message(),
                            body, headers, retryable));
                        return;
                    }

                    ResponseBody responseBody = response.body();
                    if (responseBody == null) {
                        response.close();
                        publisher.close();
                        return;
                    }

                    try (InputStream inputStream = responseBody.byteStream();
                         java.io.BufferedReader reader = new java.io.BufferedReader(
                             new java.io.InputStreamReader(inputStream, java.nio.charset.StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            if (line.startsWith("data: ")) {
                                String data = line.substring(6);
                                if (!data.isEmpty()) {
                                    try {
                                        T event = parser.apply(data);
                                        if (event != null) {
                                            publisher.submit(event);
                                        }
                                    } catch (Exception parseError) {
                                        // Skip malformed events
                                    }
                                }
                            }
                        }
                    } finally {
                        response.close();
                        publisher.close();
                    }
                } catch (Exception e) {
                    publisher.closeExceptionally(new ConnectionException("SSE stream error: " + e.getMessage()));
                }
            }
        });

        return publisher;
    }

    public <T> Flow.Publisher<T> streamSse(String path, Map<String, String> params, Function<String, T> parser) {
        SubmissionPublisher<T> publisher = new SubmissionPublisher<>();
        Request request = buildRequest("GET", path, null, params);

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                publisher.closeExceptionally(new ConnectionException("SSE stream failed: " + e.getMessage()));
            }

            @Override
            public void onResponse(Call call, Response response) {
                try {
                    if (!response.isSuccessful()) {
                        String body = response.body() != null ? response.body().string() : "";
                        response.close();
                        Map<String, String> headers = new HashMap<>();
                        response.headers().forEach(h -> headers.put(h.getName(), h.getValue()));
                        boolean retryable = response.code() >= 500 || response.code() == 429;
                        publisher.closeExceptionally(new APIException(
                            response.code(),
                            "HTTP " + response.code() + ": " + response.message(),
                            body, headers, retryable));
                        return;
                    }

                    ResponseBody responseBody = response.body();
                    if (responseBody == null) {
                        response.close();
                        publisher.close();
                        return;
                    }

                    try (InputStream inputStream = responseBody.byteStream();
                         java.io.BufferedReader reader = new java.io.BufferedReader(
                             new java.io.InputStreamReader(inputStream, java.nio.charset.StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            if (line.startsWith("data: ")) {
                                String data = line.substring(6);
                                if (!data.isEmpty()) {
                                    try {
                                        T event = parser.apply(data);
                                        if (event != null) {
                                            publisher.submit(event);
                                        }
                                    } catch (Exception parseError) {
                                        // Skip malformed events
                                    }
                                }
                            }
                        }
                    } finally {
                        response.close();
                        publisher.close();
                    }
                } catch (Exception e) {
                    publisher.closeExceptionally(new ConnectionException("SSE stream error: " + e.getMessage()));
                }
            }
        });

        return publisher;
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
