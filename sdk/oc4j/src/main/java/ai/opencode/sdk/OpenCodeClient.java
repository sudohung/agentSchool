package ai.opencode.sdk;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.api.*;
import lombok.Getter;

/**
 * Synchronous OpenCode client.
 * Provides access to all OpenCode APIs.
 */
@Getter
public class OpenCodeClient implements AutoCloseable {
    private final ClientConfig config;
    private final HttpClient http;

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

    /**
     * Create a new OpenCode client with default configuration.
     */
    public OpenCodeClient() {
        this(ClientConfig.builder().build());
    }

    /**
     * Create a new OpenCode client with custom configuration.
     * @param config client configuration
     */
    public OpenCodeClient(ClientConfig config) {
        this.config = config;
        this.http = new HttpClient(config);

        String dir = config.getDirectory();
        this.session = new SessionAPI(http, dir);
        this.message = new MessageAPI(http, dir);
        this.file = new FileAPI(http, dir);
        this.provider = new ProviderAPI(http, dir);
        this.project = new ProjectAPI(http, dir);
        this.config_api = new ConfigAPI(http, dir);
        this.agent = new AgentAPI(http, dir);
        this.command = new CommandAPI(http, dir);
        this.global = new GlobalAPI(http);
        this.permission = new PermissionAPI(http, dir);
    }

    @Override
    public void close() {
        // OkHttp client will be closed automatically
    }
}
