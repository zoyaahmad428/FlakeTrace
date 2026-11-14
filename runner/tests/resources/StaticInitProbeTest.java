import org.junit.Test;

/** Runner self-test: the static initializer throws, so the class cannot be initialized. */
public class StaticInitProbeTest {
    static int value = boom();

    static int boom() { throw new IllegalStateException("static init broke"); }

    @Test public void a() {}
    @Test public void b() {}
}
