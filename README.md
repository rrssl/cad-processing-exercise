# About

This repo contains a 3D web viewer to visualise and manipulate CAD files (2D DXF, IGES, STEP, STL).
It also offers functions to find internal corners in CAD models, where internal corners are either:
- straight edges joining two faces at an angle, or
- filleted corners (assumed to be cylinder sections) with a radius lower than 5mm.

Note that 3D DXF visualisation is not supported (as far as I know, 3D DXF files rely on the ACIS geometry kernel, which is proprietary).

# Installation

1. Install Miniconda: [link](https://docs.conda.io/en/latest/miniconda.html)
2. Create a new environment "env_name": `conda create --name env_name python=3`
3. Activate it: `conda activate env_name`
4. There are only two dependencies:
    - pythonOCC: `conda install -c conda-forge pythonocc-core=7.4.0`
    - cadquery: `conda install -c cadquery -c conda-forge cadquery=master`

Note that cadquery is only used for 2D DXF loading. While cadquery also offers OCC bindings, pythonOCC offers more utilities.

# Usage

- To check that everything was installed correctly, run `python test_corner_finder.py`
- To visualise a 3D model (e.g., "simple-rad0.step"), use `python view_model.py assets/simple-rad0.step`
- To compute and visualise internal corners, use `python view_internal_corners.py assets/simple-rad0.step`

For the last two commands, a localhost port will be given where the viewer can be accessed. It should be 8080 by default, but if the program is stopped and restarted too quickly it might be a different port.

Note that at this stage, the corner finder functionality only works for STEP files.
