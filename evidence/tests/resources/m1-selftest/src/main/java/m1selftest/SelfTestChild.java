package m1selftest;

/** Member 1's extractor test input: overrides work(); static analysis cannot know this runs. */
public class SelfTestChild extends SelfTestBase {
    @Override
    public void work() {
        System.setProperty("m1.selftest.child", "z");
    }
}
