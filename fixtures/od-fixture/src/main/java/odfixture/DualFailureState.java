package odfixture;

/** N4 fixture (ADR-010 T5): starts "unset"; a polluter sets it to a value the victim rejects. */
public class DualFailureState {
    public static int state = 0;
}
