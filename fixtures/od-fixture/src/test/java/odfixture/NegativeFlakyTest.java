package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertTrue;

/**
 * N2 negative control: intermittent failure driven by wall-clock time, unrelated
 * to any shared static field or system property and unrelated to execution order.
 * This is non-order-dependent flakiness, included so the search must not mistake
 * it for an order-dependent failure.
 */
public class NegativeFlakyTest {
    @Test
    public void sometimesFails() {
        long nanos = System.nanoTime();
        assertTrue((nanos % 2L) == 0L);
    }
}
