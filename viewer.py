import argparse

from OCC.Display.WebGl import threejs_renderer
from importers import import_file


def main():
    parser = argparse.ArgumentParser(
        description="Visualise and manipulate CAD files."
    )
    parser.add_argument('path', type=str, help="file location")
    args = parser.parse_args()

    shp = import_file(args.path)

    display = threejs_renderer.ThreejsRenderer()
    display.DisplayShape(shp)
    display.render()


if __name__ == "__main__":
    main()
