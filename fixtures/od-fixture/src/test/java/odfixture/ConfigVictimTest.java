package odfixture;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

/** F1 victim: passes alone, fails if ConfigPolluterTest#pollute ran first. */
public class ConfigVictimTest {
    @Test
    public void expectsDefaultMode() {
        assertEquals(0, Config.mode);
    }
}
