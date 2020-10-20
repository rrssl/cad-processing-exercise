import argparse

from OCC.Display.WebGl import threejs_renderer


def main():
    parser = argparse.ArgumentParser(
        description="Visualise and manipulate CAD files."
    )
    parser.add_argument('path', type=str, help="file location")
    args = parser.parse_args()

    path = args['path']
    # TODO: Load file...

    display = threejs_renderer.ThreejsRenderer()
    # TODO: Add 3D model...
    display.render()


if __name__ == "__main__":
    main()
