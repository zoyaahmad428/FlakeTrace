package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertFalse;

/**
 * F3 victim: passes alone and passes after either polluter individually.
 * Fails only when BOTH ToggleAPolluterTest#setFlagA and
 * ToggleBPolluterTest#setFlagB have run first, in either order.
 */
public class ToggleVictimTest {
    @Test
    public void expectsNotBothFlagsSet() {
        assertFalse(Toggles.flagA && Toggles.flagB);
    }
}
