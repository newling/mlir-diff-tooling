import difflib
import sys

def getStringDiff(str1_lines, str2_lines):

    # Create a Differ object
    differ = difflib.Differ()

    # Calculate the difference, do not include the lines starting with ? or -. 
    diff = list(differ.compare(str1_lines, str2_lines))
    diff = [l for l in diff if not l.startswith('?')]
    diff = [l for l in diff if not l.startswith('-')]
    return ''.join(diff)


def main(input_ir_fn, after_all_fn):
    """
    input_ir_fn  : contains the initial IR
    after_all_fn : contains the output of running passes with --print-ir-after-all
    """

    heads = []
    bodies = [[]]

    f0  = open(input_ir_fn)
    heads.append("// input IR\n")
    for l in f0.readlines():
        bodies[-1].append(l)

    f0 = open(after_all_fn)
    for l in f0.readlines():
        if "IR Dump" in l:
            heads.append(l)
            bodies.append([])
        else:
            bodies[-1].append(l)

    final = []
    final.append(heads[0])
    final.extend(bodies[0])

    nChanged = 0
    lastBody = bodies[0]
    for i in range(1, len(heads)):
        if bodies[i] != lastBody:
            final.append("\n\n")
            final.append("// line count " + str(len(lastBody)) + " -> " + str(len(bodies[i])))
            final.append("\n")
            final.append(heads[i])
            diff = getStringDiff(lastBody, bodies[i])
            final.extend(diff)
            nChanged += 1
            lastBody = bodies[i]

    print("// Number of passes that changed the IR: ", nChanged, " out of ", len(heads) - 1)
    out = ''.join(final)
    print(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("""
Usage: 
   python3 ir_diff_generator.py input.mlir after_all.mlir

Where:
   1) input.mlir
      is the input IR (which passes ran on)
   2) after_all.mlir 
      is the dump from running the MLIR passes with flags:
       --mlir-print-ir-after-all 
       --mlir-print-ir-module-scope  
       --mlir-disable-threading""")
        sys.exit(1)

    input_ir = sys.argv[1]
    after_all = sys.argv[2]

    main(input_ir, after_all)




