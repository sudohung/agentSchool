package ai.opencode.sdk;

import ai.opencode.sdk.http.AsyncHttpClient;
import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.api.*;
import lombok.Getter;

/**
 * Asynchronous OpenCode client.
 * Provides access to all OpenCode APIs with CompletableFuture support.
 */
@Getter
public class AsyncOpenCodeClient implements AutoCloseable {
    private final ClientConfig config;
    private final AsyncHttpClient asyncHttp;
    private final HttpClient syncHttp;

    private final SessionAPI session;
    private final MessageAPI message;
    private final FileAPI file;
    private final ProviderAPI provider;
    private final ProjectAPI project;
    private final ConfigAPI config_api;
    private final AgentAPI agent;
    private final CommandAPI command;
    private final GlobalAPI global;
    private final PermissionAPI permission;
    private final AsyncEventAPI event;

    /**
     * Create a new async OpenCode client with default configuration.
     */
    public AsyncOpenCodeClient() {
        this(ClientConfig.builder().build());
    }

    /**
     * Create a new async OpenCode client with custom configuration.
     * @param config client configuration
     */
    public AsyncOpenCodeClient(ClientConfig config) {
        this.config = config;
        this.asyncHttp = new AsyncHttpClient(config);
        this.syncHttp = new HttpClient(config);

        String dir = config.getDirectory();
        this.session = new SessionAPI(syncHttp, dir);
        this.message = new MessageAPI(syncHttp, dir);
        this.file = new FileAPI(syncHttp, dir);
        this.provider = new ProviderAPI(syncHttp, dir);
        this.project = new ProjectAPI(syncHttp, dir);
        this.config_api = new ConfigAPI(syncHttp, dir);
        this.agent = new AgentAPI(syncHttp, dir);
        this.command = new CommandAPI(syncHttp, dir);
        this.global = new GlobalAPI(syncHttp);
        this.permission = new PermissionAPI(syncHttp, dir);
        this.event = new AsyncEventAPI(asyncHttp, dir, config.getWorkspace());
    }

    @Override
    public void close() {
        // OkHttp client will be closed automatically
    }
}
