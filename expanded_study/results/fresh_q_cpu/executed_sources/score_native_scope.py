"""Score a closed native scope in its private NumPy environment."""
from pathlib import Path
import argparse
from run_model_suite import native_score

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--project-root',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();native_score(a.project_root.resolve(),a.output.resolve())
