package ai.opencode.sdk.model.agent;

public enum DefaultAgentEnum {
    DEFAULT_BUILD("build"),
    DEFAULT_PLAN("plan"),

    ;

    private final String value;

    DefaultAgentEnum(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
}
