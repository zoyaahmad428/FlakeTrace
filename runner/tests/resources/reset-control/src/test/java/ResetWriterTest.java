import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import org.junit.Test;

/** Leaves one piece of each kind of state behind: a static field, a system property, two files. */
public class ResetWriterTest {
    @Test
    public void leaveState() throws IOException {
        ResetState.counter = 1;
        System.setProperty(ResetState.PROPERTY, "set by ResetWriterTest");
        for (File marker : new File[] {ResetState.tempMarker(), ResetState.workingDirMarker()}) {
            try (FileWriter out = new FileWriter(marker)) {
                out.write("written by ResetWriterTest\n");
            }
            assertTrue(marker.getPath(), marker.isFile());
        }
    }
}
