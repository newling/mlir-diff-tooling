import difflib
import sys
import re

# The maximum number of lines that we will process in generating the diff.
# If the number of lines is greater than this, we will skip the diff.
maxLines = 200000

# The maximum length of a line that we will print. If a line is longer than
# this, we will replace it with a message indicating that it was trimmed.
maxLineLength = 1000


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
                elif len(l) > maxLineLength:
                    trimmed = (
                        l[0 : maxLineLength // 2]
                        + "<<<line of length "
                        + str(len(l))
                        + " was trimmed to "
                        + str(maxLineLength)
                        + " characters>>>"
                        + l[-maxLineLength // 2 :]
                    )
                    bodies[-1].append(trimmed)
                else:
                    bodies[-1].append(l)

            except UnicodeDecodeError:
                print("Error decoding line (unicode decode error).")
                break  # Stop iterating over the lines on error

    assert len(heads) == len(bodies)

    final = []
    final.append(heads[0])
    final.extend(bodies[0])

    nLines = 0
    nChanged = 0
    lastBody = bodies[0]
    passNames = []
    passNumbers = []

    fuseTrailingCleanups = False

    for i in range(1, len(heads)):
        name = heads[i].split("IR Dump After")[-1].strip().split()[0]
        if i == 1:
            passNames.append([name])
            passNumbers.append(i)

        # These are 'cleanup' passes, we're not normally interested in seeing 
        # how they change the IR. Often a pass, in the process of doing something
        # useful, creates a lot of 'fluff' that is then cleaned up by these passes.
        # Rather than showing the diff with lots of fluff, and then another differ 
        # with alot of fluff removed, we merge these fluff-removal passes into the
        # preceding pass.
        elif (fuseTrailingCleanups and name in [
            "Inliner",
            "Canonicalizer",
            "CSE",
            "DCE",
            "SymbolDCE",
            "FoldGlobals",
            "FuseGlobals",
            "AMDAIECleanup",
            ]):
            passNames[-1].append(name)
            passNumbers[-1] += 1

        else:
            passNames.append([name])
            passNumbers.append(i)

    # Merge trailing CSE / canonicalize passes into preceding passes:

    # for i in range(1, len(heads)):
    for i_ in range(1, len(passNumbers)):
        i = passNumbers[i_]
        passes = passNames[i_]

        changed = bodies[i] != lastBody
        if not changed:
            final.append("\n// IR unchanged by passes " + str(passes))

        if changed:
            nChanged += 1
            final.append("\n")
            final.append("// IR CHANGED by passes " + str(passes) + "\n")
            final.append(
                "// line count " + str(len(lastBody)) + " -> " + str(len(bodies[i]))
            )
            final.append("\n")

            if nLines < maxLines:
                diff = getStringDiff(lastBody, bodies[i])
                final.extend(diff)
            else:
                final.append("// skipping diff because line count is too high\n")

            lastBody = bodies[i]
            nLines += len(lastBody)

    print(
        "// Number of passes (canonicalization merged) that changed the IR: ",
        nChanged,
        " out of ",
        len(passNames) - 1,
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
