package ai.opencode.sdk.model.common;

import lombok.Data;

/**
 * File diff.
 */
@Data
public class FileDiff {
    private String file;
    private String before;
    private String after;
    private int additions;
    private int deletions;
    private String status;
}
