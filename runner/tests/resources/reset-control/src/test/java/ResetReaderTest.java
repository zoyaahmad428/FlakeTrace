import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;

import org.junit.Test;

/** Each method passes only if its piece of the writer's state is gone. */
public class ResetReaderTest {
    @Test
    public void staticFieldIsDefault() {
        assertEquals("static field left by an earlier test", 0, ResetState.counter);
    }

    @Test
    public void systemPropertyIsUnset() {
        assertNull("system property left by an earlier test", System.getProperty(ResetState.PROPERTY));
    }

    @Test
    public void tempFileIsAbsent() {
        assertFalse("file left in the temp folder by an earlier test", ResetState.tempMarker().exists());
    }

    @Test
    public void workingDirFileIsAbsent() {
        assertFalse("file left in the working directory by an earlier test", ResetState.workingDirMarker().exists());
    }
}
