package odfixture;

import org.junit.Test;

/** F1 polluter: sets Config.mode and never restores it. */
public class ConfigPolluterTest {
    @Test
    public void pollute() {
        Config.mode = 1;
    }
}
