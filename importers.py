from pathlib import Path
from tempfile import TemporaryDirectory

from cadquery import importers as cq_imp
from cadquery import exporters as cq_exp
from OCC.Extend.DataExchange import read_iges_file, read_step_file, read_stl_file


def read_dxf_file(path):
    """Import a 2D DXF file.

    3D DXF files are not supported because they include ACIS objects relying
    on proprietary technology.
    """
    # The cadquery package has the ability to load 2D DXF files. It used to
    # rely on pythonOCC, but now uses its own OCC python bindings instead. As a
    # workaround, this function exports the loaded file as STEP, and re-imports
    # it with pythonOCC.
    wk = cq_imp.importDXF(path)  # imports a cadquery "workspace"
    with TemporaryDirectory() as tmpdirname:
        path = str(Path(tmpdirname) / "file.step")
        cq_exp.export(wk, path)  # exports to step
        shp = read_step_file(path)
        return shp


IMPORT_METHODS = {
    'dxf': read_dxf_file,
    'iges': read_iges_file,
    'igs': read_iges_file,
    'stl': read_stl_file,
    'step': read_step_file,
    'stp': read_step_file,
}


def import_file(path):
    """Import a CAD file. Supported formats: DXF (2D only), IGES, STEP, STL.

    The format is implicitly set by the file extension.
    """
    extension = Path(path).suffix[1:].lower()
    importer = IMPORT_METHODS[extension]
    return importer(path)
