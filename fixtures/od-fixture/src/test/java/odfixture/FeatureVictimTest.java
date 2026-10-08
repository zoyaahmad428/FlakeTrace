package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertFalse;

/** F2 victim: passes alone, fails if FeaturePolluterTest#enableTurbo ran first. */
public class FeatureVictimTest {
    @Test
    public void expectsTurboDisabled() {
        assertFalse(FeatureFlags.isTurboEnabled());
    }
}
