## mlir-diff-tooling

Very basic tools for seeing how IR changes as it gets lowered through passes. 


Example:

Create a file with some IR, such as `examples/parallel_reductions.mlir`.

Run the following command to see the IR after each pass, dumped to a file. 


```
 ~/iree-build/tools/iree-compile --iree-hal-target-backends=amd-aie --mlir-print-ir-after-all --mlir-print-ir-module-scope  --mlir-disable-threading examples/parallel_reductions.mlir > ir_after_all.mlir 2>&1
```


Generate using this tool:

```
python3 mlir_diff_tooling.py examples/parallel_reductions.mlir ir_after_all.mlir > diff.html
```




