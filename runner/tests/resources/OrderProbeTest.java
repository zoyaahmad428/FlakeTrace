import static org.junit.Assert.assertEquals;

import org.junit.Test;

/** Runner self-test: b passes only if a ran before it in the same JVM; exits kills the JVM. */
public class OrderProbeTest {
    static StringBuilder log = new StringBuilder();

    @Test public void a() { log.append("a"); }
    @Test public void b() { assertEquals("a", log.toString()); }
    @Test public void exits() { System.exit(3); }
}
