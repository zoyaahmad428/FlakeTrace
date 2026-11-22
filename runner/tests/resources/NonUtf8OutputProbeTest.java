import org.junit.Test;

/** Runner self-test: prints bytes that are not UTF-8, as fastjson's tests do (0xA0, a Latin-1 non-breaking space). */
public class NonUtf8OutputProbeTest {
    @Test public void printsLatin1() {
        System.out.write(new byte[] {'o', 'k', ' ', (byte) 0xA0, '\n'}, 0, 5);
        System.err.write(new byte[] {(byte) 0xA0, '\n'}, 0, 2);
        System.out.flush();
        System.err.flush();
    }
}
