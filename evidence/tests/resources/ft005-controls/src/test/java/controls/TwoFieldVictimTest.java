package controls;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

/** Control 2, victim: reads both fields, but only State.b can make it fail. */
public class TwoFieldVictimTest {
    @Test
    public void check() {
        assertTrue(State.a >= 0);
        assertEquals(0, State.b);
    }
}
