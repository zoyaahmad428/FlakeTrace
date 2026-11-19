package odfixture;

import org.junit.Test;

/** N4 polluter: sets DualFailureState.state and never restores it. */
public class DualFailurePolluterTest {
    @Test
    public void setState() {
        DualFailureState.state = 1;
    }
}
