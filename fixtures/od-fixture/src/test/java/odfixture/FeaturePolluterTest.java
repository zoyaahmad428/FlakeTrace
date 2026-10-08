package odfixture;

import org.junit.Test;

/** F2 polluter: sets a system property and never clears it. */
public class FeaturePolluterTest {
    @Test
    public void enableTurbo() {
        System.setProperty("odfixture.turbo", "true");
    }
}
