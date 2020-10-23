import argparse

from importers import import_file
from viewer import Viewer


def main():
    parser = argparse.ArgumentParser(
        description="Visualise and manipulate CAD files."
    )
    parser.add_argument('path', type=str, help="file location")
    args = parser.parse_args()

    shp = import_file(args.path)

    display = Viewer()
    display.DisplayShape(shp, export_edges=True)
    display.render()


if __name__ == "__main__":
    main()
