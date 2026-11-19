package controls;

/** Shared static state for the two FT005 controls (W21). */
public class State {
    /** Control 1: written and then restored by the polluter. Not why the victim fails. */
    public static int restored = 0;
    /** Control 1: the real cause. The polluter sets it only through reflection. */
    public static int hidden = 0;
    /** Control 2: written by the polluter and read by the victim, but it does not matter. */
    public static int a = 0;
    /** Control 2: the field that makes the victim fail. */
    public static int b = 0;
}
