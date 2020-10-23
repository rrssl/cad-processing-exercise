import argparse

from corner_finder import find_internal_edge_corners
from corner_finder import find_internal_fillet_corners
from importers import import_file
from viewer import Viewer


def main():
    parser = argparse.ArgumentParser(
        description="Visualise the internal corners of a CAD file."
    )
    parser.add_argument('path', type=str, help="file location")
    args = parser.parse_args()

    shp = import_file(args.path)
    edges = find_internal_edge_corners(shp)
    fillets = find_internal_fillet_corners(shp)

    display = Viewer()
    display.DisplayShape(shp, export_edges=True, transparency=.3,
                         shininess=0, specular_color=(0, 0, 0))
    for face in fillets:
        display.DisplayShape(face, color=(1., 0., 0.))
    for edge in edges:
        display.DisplayShape(edge, color=(1., 0., 0.), line_width=5.)
    display.render()


if __name__ == "__main__":
    main()
