package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertTrue;

/**
 * N2 negative control: intermittent failure unrelated to any shared static field or
 * system property and unrelated to execution order. This is non-order-dependent
 * flakiness, included so the search must not mistake it for an order-dependent failure.
 *
 * Originally used {@code System.nanoTime() % 2L == 0L}. That inspects nanoTime()'s
 * lowest bit, which some JVM/OS/hardware timer combinations always zero (coarse
 * resolution -- e.g. a 100ns-granularity timer never returns an odd value), making the
 * assertion deterministically true and the test never fail there. Confirmed on a real
 * machine: Windows 11 + JDK 21 saw 0/40 failures, where Linux/JDK 8 saw a genuine ~55-60%
 * failure rate -- the exact opposite of "unrelated to the environment" this case is
 * meant to demonstrate. {@code java.util.Random}'s default seed mixes nanoTime() with a
 * per-call atomic counter through a full linear congruential generator rather than
 * exposing one raw timer bit, so it does not inherit that fragility.
 */
public class NegativeFlakyTest {
    @Test
    public void sometimesFails() {
        assertTrue(new java.util.Random().nextBoolean());
    }
}
