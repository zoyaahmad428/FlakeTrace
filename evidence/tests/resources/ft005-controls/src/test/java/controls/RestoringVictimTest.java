package controls;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

/** Control 1, victim: reads both fields; only State.hidden can make it fail. */
public class RestoringVictimTest {
    @Test
    public void check() {
        assertEquals(0, State.restored);
        assertEquals(0, State.hidden);
    }
}
