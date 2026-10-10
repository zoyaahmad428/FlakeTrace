package m1selftest;

import org.junit.Test;

/**
 * Member 1's extractor test input: reads the property that M1LifecycleSelfTest's
 * static initialiser writes, so a pair can show an edge whose write is via CLINIT.
 */
public class M1ClinitReaderSelfTest {
    @Test
    public void readsClinitProperty() {
        String value = System.getProperty("m1.selftest.clinit");
    }
}
