import org.junit.Assume;
import org.junit.BeforeClass;
import org.junit.Test;

/** Runner self-test: an assumption fails in class setup, so no test of the class runs. */
public class AssumeSetupProbeTest {
    @BeforeClass public static void once() { Assume.assumeTrue(false); }

    @Test public void a() {}
    @Test public void b() {}
}
