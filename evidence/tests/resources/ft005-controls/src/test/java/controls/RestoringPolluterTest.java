package controls;

import org.junit.Test;

/**
 * Control 1, polluter: writes State.restored and puts the old value back (a static WRITE, but no
 * lasting change), and sets State.hidden through reflection, which static analysis cannot see.
 */
public class RestoringPolluterTest {
    @Test
    public void pollute() throws Exception {
        int old = State.restored;
        State.restored = 42;
        State.restored = old;
        State.class.getField("hidden").setInt(null, 1);
    }
}
