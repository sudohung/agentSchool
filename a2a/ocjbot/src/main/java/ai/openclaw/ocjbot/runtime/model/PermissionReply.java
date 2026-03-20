package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PermissionReply {
    
    public enum ReplyType {
        ONCE,
        ALWAYS,
        REJECT
    }
    
    private String permissionId;
    private ReplyType reply;
    private String message;
    
    public static PermissionReply once() {
        return PermissionReply.builder()
            .reply(ReplyType.ONCE)
            .build();
    }
    
    public static PermissionReply always() {
        return PermissionReply.builder()
            .reply(ReplyType.ALWAYS)
            .build();
    }
    
    public static PermissionReply reject() {
        return PermissionReply.builder()
            .reply(ReplyType.REJECT)
            .build();
    }
}