import java.io.File;

/** FT021 reset control: the state the writer leaves and the readers look for (ADR-012 section 1). */
final class ResetState {
    static final String PROPERTY = "flaketrace.reset.control";
    static final String MARKER = "flaketrace-reset-control.marker";
    static int counter = 0;

    static File tempMarker() {
        return new File(System.getProperty("java.io.tmpdir"), MARKER);
    }

    static File workingDirMarker() {
        return new File(System.getProperty("user.dir"), MARKER);
    }

    private ResetState() {
    }
}
