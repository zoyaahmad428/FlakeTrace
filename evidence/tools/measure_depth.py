"""Measure what each --depth adds: accesses, unsupported observations, javap calls, time.

Runs the extractor on every test method of a compiled project at depths 1, 2 and 3,
REPEATS times per depth, each time with an empty class cache (a fresh Project), and
prints the totals and the median wall time per depth.

Usage (from the repository root):
    python3 -m evidence.tools.measure_depth --classes DIR --test-classes DIR [--repeats 5]
"""
import argparse
import os
import statistics
import time

from evidence import extract


def list_test_methods(project, test_classes_dir):
    """Class#method for every JUnit 4 @Test method and every JUnit 3 public void test*()."""
    tests = []
    for root, _, files in os.walk(test_classes_dir):
        for name in sorted(files):
            if not name.endswith(".class") or "$" in name:
                continue
            relative = os.path.relpath(os.path.join(root, name), test_classes_dir)
            class_name = relative[:-len(".class")].replace(os.sep, ".")
            chain = project.superclass_chain(class_name)
            junit3 = bool(chain) and chain[-1].super_name == extract.JUNIT3_BASE
            for method in project.load(class_name).methods:
                junit4 = "org/junit/Test" in method.annotations
                junit3_test = (junit3 and method.name.startswith("test") and method.descriptor == "()V"
                               and "ACC_PUBLIC" in method.flags)
                if junit4 or junit3_test:
                    tests.append("%s#%s" % (class_name, method.name))
    return sorted(tests)


def measure(class_dirs, tests, depth):
    project = extract.Project(class_dirs)          # empty cache: javap time is included
    start = time.perf_counter()
    accesses = unsupported = 0
    for test in tests:
        result = extract.analyse_test(project, test, depth)
        accesses += len(result["accesses"])
        unsupported += len(result["unsupported_observations"])
    return accesses, unsupported, len(project.cache), time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser(prog="python3 -m evidence.tools.measure_depth")
    parser.add_argument("--classes", required=True)
    parser.add_argument("--test-classes", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    class_dirs = [args.classes, args.test_classes]
    tests = list_test_methods(extract.Project(class_dirs), args.test_classes)
    print("javap %s; %d test methods; %d repeats per depth" %
          (extract.javap_version(), len(tests), args.repeats))
    print("depth  accesses  unsupported  javap_calls  median_s  min_s  max_s")
    for depth in (1, 2, 3):
        runs = [measure(class_dirs, tests, depth) for _ in range(args.repeats)]
        accesses, unsupported, calls, _ = runs[0]
        times = [r[3] for r in runs]
        assert all(r[:3] == runs[0][:3] for r in runs), "counts differ between repeats"
        print("%5d  %8d  %11d  %11d  %8.3f  %5.3f  %5.3f" % (
            depth, accesses, unsupported, calls, statistics.median(times), min(times), max(times)))


if __name__ == "__main__":
    main()
