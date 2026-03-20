package ai.openclaw.ocjbot.gateway;

import ai.openclaw.ocjbot.config.OcjbotConfig;
import ai.openclaw.ocjbot.harness.Harness;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.http.*;
import io.netty.handler.codec.http.websocketx.WebSocketServerProtocolHandler;
import io.netty.handler.stream.ChunkedWriteHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

public class GatewayServer {
    private static final Logger log = LoggerFactory.getLogger(GatewayServer.class);
    
    private final Harness harness;
    private final OcjbotConfig config;
    private EventLoopGroup bossGroup;
    private EventLoopGroup workerGroup;
    private Channel mainChannel;
    
    public GatewayServer(Harness harness, OcjbotConfig config) {
        this.harness = harness;
        this.config = config;
    }
    
    public void start() {
        bossGroup = new NioEventLoopGroup(1);
        workerGroup = new NioEventLoopGroup();
        
        try {
            ServerBootstrap bootstrap = new ServerBootstrap();
            bootstrap.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ChannelPipeline pipeline = ch.pipeline();
                        pipeline.addLast(new HttpServerCodec());
                        pipeline.addLast(new HttpObjectAggregator(65536));
                        pipeline.addLast(new ChunkedWriteHandler());
                        pipeline.addLast(new WebSocketServerProtocolHandler("/ws"));
                        pipeline.addLast(new GatewayHandler(harness, config));
                    }
                })
                .option(ChannelOption.SO_BACKLOG, 128)
                .childOption(ChannelOption.SO_KEEPALIVE, true);
            
            mainChannel = bootstrap.bind(
                config.getGateway().getHost(),
                config.getGateway().getPort()
            ).sync().channel();
            
            log.info("Gateway Server started on http://{}:{}", 
                config.getGateway().getHost(), config.getGateway().getPort());
            log.info("WebSocket endpoint: ws://{}:{}/ws", 
                config.getGateway().getHost(), config.getGateway().getPort());
            
        } catch (InterruptedException e) {
            log.error("Failed to start Gateway server", e);
            Thread.currentThread().interrupt();
        }
    }
    
    public void stop() {
        log.info("Stopping Gateway Server...");
        
        if (mainChannel != null) {
            mainChannel.close();
        }
        
        if (workerGroup != null) {
            workerGroup.shutdownGracefully();
        }
        
        if (bossGroup != null) {
            bossGroup.shutdownGracefully();
        }
        
        log.info("Gateway Server stopped.");
    }
}

class GatewayHandler extends SimpleChannelInboundHandler<FullHttpRequest> {
    private static final Logger log = LoggerFactory.getLogger(GatewayHandler.class);
    
    private final Harness harness;
    private final OcjbotConfig config;
    private boolean isWebSocket = false;
    
    public GatewayHandler(Harness harness, OcjbotConfig config) {
        this.harness = harness;
        this.config = config;
    }
    
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, FullHttpRequest request) throws Exception {
        String uri = request.uri();
        
        if (uri.startsWith("/ws")) {
            isWebSocket = true;
            ctx.fireChannelRead(request.retain());
            return;
        }
        
        if (uri.startsWith("/api/")) {
            handleApiRequest(ctx, request, uri);
            return;
        }
        
        serveStaticFile(ctx, request, uri);
    }
    
    private void handleApiRequest(ChannelHandlerContext ctx, FullHttpRequest request, String uri) {
        String method = request.method().name();
        String response;
        String contentType = "application/json";
        
        try {
            if (uri.equals("/api/health")) {
                response = "{\"status\":\"UP\",\"version\":\"2.1.0\"}";
            } else if (uri.equals("/api/sessions") && "GET".equals(method)) {
                response = "{\"sessions\":[]}";
            } else if (uri.equals("/api/runtime/info") && "GET".equals(method)) {
                response = "{\"type\":\"Mock\",\"healthy\":true,\"name\":\"Mock Runtime\"}";
            } else {
                response = "{\"error\":\"Not found\"}";
                sendResponse(ctx, HttpResponseStatus.NOT_FOUND, response, contentType);
                return;
            }
            
            sendResponse(ctx, HttpResponseStatus.OK, response, contentType);
            
        } catch (Exception e) {
            log.error("API error", e);
            sendResponse(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, 
                "{\"error\":\"" + e.getMessage() + "\"}", contentType);
        }
    }
    
    private void serveStaticFile(ChannelHandlerContext ctx, FullHttpRequest request, String uri) {
        String path = uri.equals("/") ? "/web/index.html" : "/web" + uri;
        
        try {
            URL resource = getClass().getResource(path);
            
            if (resource == null) {
                String notFound = "<html><body><h1>404 Not Found</h1></body></html>";
                sendResponse(ctx, HttpResponseStatus.NOT_FOUND, notFound, "text/html");
                return;
            }
            
            String content = readResource(path);
            String contentType = getContentType(path);
            sendResponse(ctx, HttpResponseStatus.OK, content, contentType);
            
        } catch (Exception e) {
            log.error("Failed to serve static file: {}", path, e);
            sendResponse(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, 
                "<html><body><h1>500 Internal Server Error</h1></body></html>", "text/html");
        }
    }
    
    private String readResource(String path) throws IOException {
        try (InputStream is = getClass().getResourceAsStream(path)) {
            if (is == null) {
                throw new FileNotFoundException("Resource not found: " + path);
            }
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
    
    private String getContentType(String path) {
        if (path.endsWith(".html")) return "text/html";
        if (path.endsWith(".css")) return "text/css";
        if (path.endsWith(".js")) return "application/javascript";
        if (path.endsWith(".json")) return "application/json";
        if (path.endsWith(".png")) return "image/png";
        if (path.endsWith(".svg")) return "image/svg+xml";
        return "text/plain";
    }
    
    private void sendResponse(ChannelHandlerContext ctx, HttpResponseStatus status, 
                              String content, String contentType) {
        byte[] bytes = content.getBytes(StandardCharsets.UTF_8);
        
        FullHttpResponse response = new DefaultFullHttpResponse(
            HttpVersion.HTTP_1_1, 
            status,
            Unpooled.wrappedBuffer(bytes)
        );
        
        response.headers().set(HttpHeaderNames.CONTENT_TYPE, contentType + "; charset=UTF-8");
        response.headers().set(HttpHeaderNames.CONTENT_LENGTH, bytes.length);
        response.headers().set(HttpHeaderNames.ACCESS_CONTROL_ALLOW_ORIGIN, "*");
        
        ctx.writeAndFlush(response);
    }
    
    @Override
    public void userEventTriggered(ChannelHandlerContext ctx, Object evt) throws Exception {
        if (evt instanceof WebSocketServerProtocolHandler.HandshakeComplete) {
            log.info("WebSocket connection established: {}", ctx.channel().id().asShortText());
            sendWelcome(ctx);
        }
        super.userEventTriggered(ctx, evt);
    }
    
    private void sendWelcome(ChannelHandlerContext ctx) {
        Map<String, Object> welcome = new HashMap<>();
        welcome.put("type", "welcome");
        welcome.put("message", "Welcome to OCJBot Gateway");
        welcome.put("version", "2.1.0");
        welcome.put("runtime", "Mock");
        
        sendWsMessage(ctx, welcome);
    }
    
    private void sendWsMessage(ChannelHandlerContext ctx, Map<String, Object> message) {
        try {
            String json = new com.fasterxml.jackson.databind.ObjectMapper()
                .writeValueAsString(message);
            ctx.writeAndFlush(new TextWebSocketFrame(json));
        } catch (Exception e) {
            log.error("Failed to send WS message", e);
        }
    }
    
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        if (!isWebSocket) {
            log.error("Gateway error", cause);
        }
        ctx.close();
    }
}