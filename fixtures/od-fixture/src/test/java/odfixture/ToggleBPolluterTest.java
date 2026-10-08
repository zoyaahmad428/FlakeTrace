package odfixture;

import org.junit.Test;

/** F3 polluter 2 of 2: sets flagB only. Alone, this does not break the victim. */
public class ToggleBPolluterTest {
    @Test
    public void setFlagB() {
        Toggles.flagB = true;
    }
}
