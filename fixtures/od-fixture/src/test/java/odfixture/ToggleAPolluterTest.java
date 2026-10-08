package odfixture;

import org.junit.Test;

/** F3 polluter 1 of 2: sets flagA only. Alone, this does not break the victim. */
public class ToggleAPolluterTest {
    @Test
    public void setFlagA() {
        Toggles.flagA = true;
    }
}
