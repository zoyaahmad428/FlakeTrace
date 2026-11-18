package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

/** N4 victim (ADR-010 T5): throws IllegalStateException alone (state never set), and
 * AssertionError after DualFailurePolluterTest#setState (state is 1, not the expected 2) --
 * two DIFFERENT failures, neither of which is a pass. Regression fixture for FT003: the Mid
 * build counted only alone failures matching the reference signature, so this victim's real
 * IllegalStateException alone read as "never failed alone" and would have named the polluter
 * wrongly as VERIFIED. */
public class DualFailureVictimTest {
    @Test
    public void expectsStateTwo() {
        if (DualFailureState.state == 0) {
            throw new IllegalStateException("DualFailureState.state was never set");
        }
        assertEquals(2, DualFailureState.state);
    }
}
