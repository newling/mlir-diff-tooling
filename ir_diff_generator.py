import difflib
import sys
import re


def fillMinus(l):
    """
    Takes in a string (single line) which starts with -, afollowed by n space
    characters, and then optionally followed by other characters. Replaces spaces
    with '-'. Example:

    "-  xy" becomes "---xy"
    "-"     becomes "-"
    "-     w-" becomes "------w-"
    etc.

    More generally, "[-][n spaces][other chars]" becomes "[n+1 -][other chars]"
    """
    assert l.startswith("-")
    n = 1
    while n < len(l) and l[n] == " ":
        n += 1

    return "-" * (n) + l[n:]


def sameUpToSSAVals(l1, l2):
    """
    return True if l1 and l2 are effectively the same, except that SSA values 
    %0, %1, etc. may differ.
    """
    s = r"%[A-Za-z0-9_]+"
    return re.sub(s, "", l1) == re.sub(s, "", l2)


def getStringDiff(str1_lines, str2_lines):
    differ = difflib.Differ()
    diff = list(differ.compare(str1_lines, str2_lines))
    diff = [x for x in diff if not x.startswith("?")]
    newDiff = []

    decrease = len(str1_lines) >= len(str2_lines)

    def uninterestingChange(i, targetStart):
        l = diff[i]
        for k in [1, -1]:
            j = i + k
            if j >= 0 and j < len(diff):
                l2 = diff[j]
                # squeeze out all trailing spaces from l:
                if l2.startswith(targetStart) and sameUpToSSAVals(
                    l[1::].strip(), l2[1::].strip()
                ):
                    return True
        return False

    for i in range(len(diff)):
        l = diff[i]
        if l.startswith("-"):
            # only print removal lines if they're interesting.
            if decrease and not uninterestingChange(i, "+"):
                newDiff.append(fillMinus(l))

        elif l.startswith("+"):
            # only include '+' on new lines if they're interesting.
            if not uninterestingChange(i, "-"):
                newDiff.append(l)
            else:
                newDiff.append(" " + l[1::])
        else:
            newDiff.append(l)

    return "".join(newDiff)


def main(input_ir_fn, after_all_fn):
    """
    input_ir_fn  : contains the initial IR
    after_all_fn : contains the output of running passes with --print-ir-after-all
    """

    f0 = open(input_ir_fn)
    heads = ["// input IR\n"]

    bodies = [[]]
    for l in f0.readlines():
        bodies[-1].append(l)

    
    with open(after_all_fn, "r", encoding="utf-8", errors="ignore") as f0:

        for l in f0:

            try:
                if "IR Dump" in l:
                    heads.append(l)
                    bodies.append([])
                else:
                    bodies[-1].append(l)

            except UnicodeDecodeError:
                break  # Stop iterating over the lines on error
    
    
    assert len(heads) == len(bodies)

    final = []
    final.append(heads[0])
    final.extend(bodies[0])

    nLines = 0
    nChanged = 0
    lastBody = bodies[0]
    for i in range(1, len(heads)):
        if bodies[i] != lastBody:
            nChanged += 1
            final.append("\n\n")
            final.append(heads[i])
            final.append(
                "// line count " + str(len(lastBody)) + " -> " + str(len(bodies[i]))
            )
            final.append("\n")

            if nLines < 10000:
                diff = getStringDiff(lastBody, bodies[i])
                final.extend(diff)
            else:
                final.append("// skipping diff because line count is too high\n")


            lastBody = bodies[i]
            nLines += len(lastBody)

    print(
        "// Number of passes that changed the IR: ",
        nChanged,
        " out of ",
        len(heads) - 1,
    )
    out = "".join(final)
    print(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            """
Usage: 
   python3 ir_diff_generator.py input.mlir after_all.mlir

Where:
   1) input.mlir
      is the input IR (which passes ran on)
   2) after_all.mlir 
      is the dump from running the MLIR passes with flags:
       --mlir-print-ir-after-all 
       --mlir-print-ir-module-scope  
       --mlir-disable-threading"""
        )
        sys.exit(1)

    input_ir = sys.argv[1]
    after_all = sys.argv[2]

    main(input_ir, after_all)
