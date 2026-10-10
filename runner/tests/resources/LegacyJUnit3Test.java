import junit.framework.TestCase;

/** A JUnit 3 TestCase with an order-dependent pair, run through FtHarness by test_order_runner.py. */
public class LegacyJUnit3Test extends TestCase {
    static int state = 0;

    public void testPollute() {
        state = 1;
    }

    public void testVictim() {
        assertEquals(0, state);
    }
}
