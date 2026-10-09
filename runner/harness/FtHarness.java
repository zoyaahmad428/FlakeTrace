import java.io.BufferedReader;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;

import org.junit.internal.runners.ErrorReportingRunner;
import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.Request;
import org.junit.runner.Runner;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

/**
 * Runs the tests listed on stdin ("Class#method", one per line) in that exact order, in this
 * one JVM, and writes one tab-separated result line per test to the file named in args[0].
 * With "--list <file>", reads class names instead and writes each class's test methods as
 * "Class#method", in the order JUnit would run them (ADR-004).
 * Launched by runner/order_runner.py; see ADR-003.
 */
public class FtHarness {

    public static void main(String[] args) throws Exception {
        if (args[0].equals("--list")) {
            list(args[1]);
            System.exit(0);
        }
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        PrintStream out = new PrintStream(new FileOutputStream(args[0]), true, "UTF-8");
        int index = 0;
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            out.println(index + "\t" + line + "\t" + runOne(line));
            index++;
        }
        out.close();
        // Tests may leave non-daemon threads running; exit so the JVM never hangs after the last test.
        System.exit(0);
    }

    static void list(String resultFile) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        PrintStream out = new PrintStream(new FileOutputStream(resultFile), true, "UTF-8");
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            Runner runner;
            try {
                runner = Request.aClass(Class.forName(line)).getRunner();
            } catch (Throwable t) {
                continue;  // a class that cannot even load cannot be run either
            }
            if (runner instanceof ErrorReportingRunner) {
                continue;  // abstract class, or no @Test methods
            }
            for (Description child : runner.getDescription().getChildren()) {
                if (child.isTest() && child.getMethodName() != null) {
                    out.println(line + "#" + child.getMethodName());
                }
            }
        }
        out.close();
    }

    static String runOne(String spec) {
        int hash = spec.indexOf('#');
        Class<?> cls;
        try {
            cls = Class.forName(spec.substring(0, hash));
        } catch (Throwable t) {
            return format("FAIL", t);
        }
        final Throwable[] failure = new Throwable[1];
        final boolean[] skipped = new boolean[1];
        JUnitCore core = new JUnitCore();
        core.addListener(new RunListener() {
            @Override
            public void testFailure(Failure f) {
                failure[0] = f.getException();
            }

            @Override
            public void testAssumptionFailure(Failure f) {
                skipped[0] = true;
            }

            @Override
            public void testIgnored(Description d) {
                skipped[0] = true;
            }
        });
        core.run(Request.method(cls, spec.substring(hash + 1)));
        if (failure[0] != null) {
            return format("FAIL", failure[0]);
        }
        return skipped[0] ? "SKIP\t\t\t" : "PASS\t\t\t";
    }

    static String format(String status, Throwable t) {
        StringBuilder frames = new StringBuilder();
        for (StackTraceElement e : t.getStackTrace()) {
            if (frames.length() > 0) {
                frames.append('|');
            }
            frames.append(e.getClassName()).append('.').append(e.getMethodName())
                  .append(':').append(e.getLineNumber());
        }
        String message = t.getMessage() == null ? "" : t.getMessage();
        return status + "\t" + t.getClass().getName() + "\t" + escape(message) + "\t" + escape(frames.toString());
    }

    static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r");
    }
}
