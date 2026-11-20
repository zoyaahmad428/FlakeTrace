package controls;

import org.junit.Test;

/** Control 2, polluter: writes two fields; the victim depends on only one of them. */
public class TwoFieldPolluterTest {
    @Test
    public void pollute() {
        State.a = 1;
        State.b = 1;
    }
}
