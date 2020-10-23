from OCC.Core.gp import gp_Trsf
from OCC.Core.gp import gp_Vec
from OCC.Core.BRep import BRep_Tool_Continuity
from OCC.Core.BRep import BRep_Tool_Curve
from OCC.Core.BRep import BRep_Tool_Parameters
from OCC.Core.BRep import BRep_Tool_Pnt
from OCC.Core.BRep import BRep_Tool_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepLProp import BRepLProp_SLProps
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.Geom import Geom_Line
from OCC.Core.Geom import Geom_Plane
from OCC.Core.GeomAbs import GeomAbs_C0
from OCC.Core.TopAbs import TopAbs_REVERSED
from OCC.Extend.TopologyUtils import TopologyExplorer
# from OCC.Extend.TopologyUtils import dump_topology_to_string

MAX_FILLET_RADIUS = 5.


def get_edge_line(edge):
    """Get the geometric line segment associated to this edge.

    If the edge is not a line segment, None is returned.
    """
    # While BRep_Tool_Surface returns a Geom_Surface directly,
    # BRep_Tool_Curve returns a tuple (Geom_Curve, float, float).
    return Geom_Line.DownCast(BRep_Tool_Curve(edge)[0])


def get_face_cylinder(face):
    """Get the geometric cylinder section associated to this face.

    If the face is not a cylinder section, None is returned.
    """
    return Geom_CylindricalSurface.DownCast(BRep_Tool_Surface(face))


def get_face_plane(face):
    """Get the geometric plane associated to this face.

    If the face is not a plane, None is returned.
    """
    return Geom_Plane.DownCast(BRep_Tool_Surface(face))


def get_face_normal_at_vertex(face, vertex):
    """Get the face normal at this vertex. The normal points outwards.

    The vertex is assumed to belong to this face.
    """
    vertex_uv = BRep_Tool_Parameters(vertex, face)
    slprops = BRepLProp_SLProps(
        BRepAdaptor_Surface(face),
        vertex_uv.X(),
        vertex_uv.Y(),
        2, 1e-6
    )
    normal = slprops.Normal()
    if face.Orientation() == TopAbs_REVERSED:
        normal.Reverse()
    return normal


def get_translated_face(face, tr):
    """Get a translated copy of this face."""
    if type(tr) is not gp_Vec:
        tr = gp_Vec(tr)
    xform = gp_Trsf()
    xform.SetTranslation(tr)
    return BRepBuilderAPI_Transform(face, xform, True).Shape()


def find_internal_fillet_corners(model):
    model_explorer = TopologyExplorer(model)
    corner_faces = []
    for face in model_explorer.faces():
        # 1. Check if the face is a fillet corner.
        # A fillet corner is a cylinder section that connects two faces with
        # straight edges and a differentiable boundary.
        fillet = get_face_cylinder(face)
        if fillet is None:
            continue
        # Try to find two straight edges. For now we're going to assume that
        # each straight edge is in a single piece, meaning that there shouldn't
        # be more than two.
        straight_edges = []
        for edge in model_explorer.edges_from_face(face):
            line = get_edge_line(edge)
            if line is None:
                continue
            straight_edges.append(edge)
        if len(straight_edges) < 2:
            continue
        # Check that the faces on each side of the fillet are distinct.
        side_faces_with_edge = []
        for edge in straight_edges:
            f1, f2 = model_explorer.faces_from_edge(edge)
            other_face = f1 if face == f2 else f2
            side_faces_with_edge.append((other_face, edge))
        if side_faces_with_edge[0][0] == side_faces_with_edge[1][0]:
            continue
        # Check the continuity of the faces at these edges.
        is_continuous = True
        for side_face, edge in side_faces_with_edge:
            continuity = BRep_Tool_Continuity(edge, face, side_face)
            if continuity == GeomAbs_C0:
                is_continuous = False
                break
        if not is_continuous:
            continue
        # 2. Check the radius of the fillet. It has to be under a predefined
        # value to qualify as a corner.
        radius = fillet.Radius()
        if radius >= MAX_FILLET_RADIUS:
            continue
        # 3. Check that this is an interior corner.
        # We use the following method:
        # a. Compute the shortest distance between the side faces, D.
        # b. Translate each side face along its outwards normal, and recompute
        # the shortest distance between the now translated side faces, D'.
        # c. If the faces got closer (D > D'), then it is an internal corner.
        # ---
        # Compute each face's normal at some point along their respective edge.
        f1, f1_edge = side_faces_with_edge[0]
        f1_vertex = next(model_explorer.vertices_from_edge(f1_edge))
        n1 = get_face_normal_at_vertex(f1, f1_vertex)
        f2, f2_edge = side_faces_with_edge[1]
        f2_vertex = next(model_explorer.vertices_from_edge(f2_edge))
        n2 = get_face_normal_at_vertex(f2, f2_vertex)
        # Compute the initial shortest distance between the side faces.
        dist = BRepExtrema_DistShapeShape(f1, f2).Value()
        # Get a copy of each face translated along their respective normals.
        tr_dist = 1e-1
        f1_tr = get_translated_face(f1, gp_Vec(n1)*tr_dist)
        f2_tr = get_translated_face(f2, gp_Vec(n2)*tr_dist)
        # Compute the new shortest distance between the side faces.
        dist_tr = BRepExtrema_DistShapeShape(f1_tr, f2_tr).Value()
        # Compare the distances.
        if dist > dist_tr:
            corner_faces.append(face)
    return corner_faces


def find_internal_edge_corners(model):
    # For edge corners, there are several ways to check for internality.
    # A first method would be to find a point on each side face, close to the
    # edge but not exactly on it, and then compute
    #   dot = (x2 - x1).Dot(n1)
    # If dot > 0, then it is an internal edge.
    # The tricky part is computing the point on each side face. It cannot be
    # anywhere on the face, because the face might not be convex.
    # A second method (implemented here) avoids relying on a specific point.
    # Instead, each side face is translated (by a small amount) along its
    # outwards normal. If the translated faces intersect, then we have an
    # internal corner.
    model_explorer = TopologyExplorer(model)
    corner_edges = []
    # Iterate over edges
    for edge in model_explorer.edges():
        # Get the 2 faces sharing this edge.
        try:
            f1, f2 = model_explorer.faces_from_edge(edge)
        except ValueError:
            continue
        # Ensure that the interface is not differentiable (C0 max).
        continuity = BRep_Tool_Continuity(edge, f1, f2)
        if continuity > GeomAbs_C0:
            continue
        # Compute each face's normal at some point along the edge.
        edge_vertex = next(model_explorer.vertices_from_edge(edge))
        n1 = get_face_normal_at_vertex(f1, edge_vertex)
        n2 = get_face_normal_at_vertex(f2, edge_vertex)
        # Get a copy of each face translated along their respective normals.
        # No need to translate by a lot, as the faces share an edge.
        tr_dist = 1e-1
        f1_tr = get_translated_face(f1, gp_Vec(n1)*tr_dist)
        f2_tr = get_translated_face(f2, gp_Vec(n2)*tr_dist)
        # If translated faces intersect, then it is a interior corner.
        dist = BRepExtrema_DistShapeShape(f1_tr, f2_tr).Value()
        if dist < 1e-6:
            print("Found an internal edge corner")
            corner_edges.append(edge)
    return corner_edges
