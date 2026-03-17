package ai.opencode.sdk.model.common;

import lombok.Data;
import java.util.List;

/**
 * Session summary.
 */
@Data
public class SessionSummary {
    private int additions;
    private int deletions;
    private int files;
    private List<FileDiff> diffs;
}
