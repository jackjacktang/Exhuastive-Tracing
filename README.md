# Exhaustive tracing

## Dependencies
pip3 install -r requirements.txt
The package quirements for running:

* scipy>=1.1.0
* numpy>=1.16.0
* matplotlib>=2.2.2
* pyglet>=1.3.0
* scikit_image>=0.14.0
* scikit_fmm>=2019.1.30
* Pillow>=6.1.0


```bash
usage: rtrace -f FILE -o OUT [--threshold] [--coverage_ratio]
              [--allow_gap] [--trace] [--dt] [--iter]

Arguments to perform the Rivulet2 tracing algorithm.

optional arguments:
  --file                The input file. A image file (*.tif, *.nii, *.mat).
  --out                 The name of the output file
  --threshold           threshold to distinguish the foreground and
                        background. Default 0.
```

## Sample Usage:

```bash
python main.py --file path/to/input --threshold 0 --out path/to/output
