import unittest

from corner_finder import (find_internal_edge_corners,
                           find_internal_fillet_corners)
from importers import import_file


class TestCornerFinder(unittest.TestCase):

    def test_plane2plane_edge_corner(self):
        model = import_file("assets/simple-rad0.step")
        edges = find_internal_edge_corners(model)
        self.assertEqual(len(edges), 3)

    def test_plane2cylinder_edge_corner(self):
        model = import_file("assets/simple-with-cyl.step")
        edges = find_internal_edge_corners(model)
        self.assertEqual(len(edges), 5)

    def test_plane2plane_fillet_corner(self):
        model = import_file("assets/simple-rad1int1ext.step")
        fillets = find_internal_fillet_corners(model)
        self.assertEqual(len(fillets), 1)

    def test_fillet_corner_max_size(self):
        model = import_file("assets/simple-rad1and5.step")
        fillets = find_internal_fillet_corners(model)
        self.assertEqual(len(fillets), 1)


if __name__ == "__main__":
    unittest.main()
