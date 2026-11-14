import org.junit.BeforeClass;
import org.junit.Test;

/** Runner self-test: class setup fails, so no test of the class can run. */
public class BrokenSetupProbeTest {
    @BeforeClass public static void once() { throw new IllegalStateException("setup broke"); }

    @Test public void a() {}
    @Test public void b() {}
}
