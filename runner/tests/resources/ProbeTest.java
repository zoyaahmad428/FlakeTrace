import java.io.File;

import org.junit.Ignore;
import org.junit.Test;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

/** Probe tests for runner/tests/test_order_runner.py — edge cases the fixture does not contain. */
public class ProbeTest {

    @Test
    public void failsWithFormFeed() {
        fail("page\fbreak");
    }

    @Test
    public void needsPomInWorkingDir() {
        assertTrue(new File("pom.xml").exists());
    }

    @Test
    public void exitsTheJvm() {
        System.exit(3);
    }

    @Ignore
    @Test
    public void ignored() {
    }
}
