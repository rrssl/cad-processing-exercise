import uuid
import os
import sys

from OCC.Core.Tesselator import ShapeTesselator
from OCC.Display.WebGl import threejs_renderer
from OCC.Display.WebGl.threejs_renderer import export_edgedata_to_json
from OCC.Display.WebGl.threejs_renderer import THREEJS_RELEASE
from OCC.Extend.TopologyUtils import is_edge
from OCC.Extend.TopologyUtils import is_wire
from OCC.Extend.TopologyUtils import discretize_edge
from OCC.Extend.TopologyUtils import discretize_wire


# The code below is mostly coped from pythonOCC, with changes to improve the
# display.
threejs_renderer.HEADER = """
<head>
    <title>pythonocc @VERSION@ webgl renderer</title>
    <meta name='Author' content='Thomas Paviot - tpaviot@gmail.com'>
    <meta name='Keywords' content='WebGl,pythonocc'>
    <meta charset="utf-8">
    <style>
        body {
            background: linear-gradient(@bg_gradient_color1@, @bg_gradient_color2@);
            margin: 0px;
            overflow: hidden;
        }
        #commands {
            padding: 5px;
            position: absolute;
            right: 1%;
            top: 2%;
            height: 95px;
            width: 120px;
            border-radius: 5px;
            border: 2px solid #f7941e;
            opacity: 0.7;
            font-family: Arial;
            background-color: #414042;
            color: #ffffff;
            font-size: 14px;
            opacity: 0.5;
        }
    </style>
</head>
"""
threejs_renderer.BODY_PART0 = """
<body>
    <div id="container"></div>
    <div id="commands">
    <b>left mouse</b> rotate<br>
    <b>right mouse</b> pan<br>
    <b>scroll</b> zoom in/out<br>
    <b>t</b> view/hide shape<br>
    <b>g</b> view/hide grid<br>
    <b>a</b> view/hide axis<br>
    </div>
    <script src="https://rawcdn.githack.com/mrdoob/three.js/%s/build/three.min.js"></script>
    <script src="https://rawcdn.githack.com/mrdoob/three.js/%s/examples/js/controls/TrackballControls.js"></script>
    <script src="https://rawcdn.githack.com/mrdoob/three.js/%s/examples/js/libs/stats.min.js"></script>
""" % (THREEJS_RELEASE, THREEJS_RELEASE, THREEJS_RELEASE)
threejs_renderer.BODY_PART2 = """
            renderer = new THREE.WebGLRenderer({antialias:true, alpha: true});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio( window.devicePixelRatio );
            container.appendChild(renderer.domElement);
            //renderer.gammaInput = true;
            //renderer.gammaOutput = true;
            // for shadow rendering
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFShadowMap;
            controls = new THREE.TrackballControls(camera, renderer.domElement);
            // show stats, is it really useful ?
            stats = new Stats();
            stats.domElement.style.position = 'absolute';
            stats.domElement.style.top = '2%';
            stats.domElement.style.left = '1%';
            container.appendChild(stats.domElement);
            // add events
            document.addEventListener('keypress', onDocumentKeyPress, false);
            document.addEventListener('click', onDocumentMouseClick, false);
            window.addEventListener('resize', onWindowResize, false);
        }
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            render();
            stats.update();
        }
        function update_lights() {
            if (directionalLight != undefined) {
                directionalLight.position.copy(camera.position);
            }
        }
        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }
        function onDocumentKeyPress(event) {
          event.preventDefault();
          if (event.key=="t") {  // t key
              if (selected_target) {
                    selected_target.material.visible = !selected_target.material.visible;
                }
          }
          else if (event.key=="g") { // g key, toggle grid visibility
               gridHelper.visible = !gridHelper.visible;
          }
          else if (event.key=="a") { // g key, toggle axisHelper visibility
               axisHelper.visible = !axisHelper.visible;
          }
          else if (event.key=="w") { // g key, toggle axisHelper visibility
               if (selected_target) {
                    selected_target.material.wireframe = !selected_target.material.wireframe;
                }
          }
        }
        function onDocumentMouseClick(event) {
            event.preventDefault();
            mouse.x = ( event.clientX / window.innerWidth ) * 2 - 1;
            mouse.y = - ( event.clientY / window.innerHeight ) * 2 + 1;
            // restore previous selected target color
            if (selected_target) {
                selected_target.material.color.setRGB(selected_target_color_r,
                    selected_target_color_g,
                    selected_target_color_b);
            }
            // perform selection
            raycaster.setFromCamera(mouse, camera);
            var intersects = raycaster.intersectObjects(scene.children);
            if (intersects.length > 0) {
                var target = intersects[0].object;
                selected_target_color_r = target.material.color.r;
                selected_target_color_g = target.material.color.g;
                selected_target_color_b = target.material.color.b;
                target.material.color.setRGB(1., 0.65, 0.);
                console.log(target);
                selected_target = target;
            }
        }
        function fit_to_scene() {
            // compute bounding sphere of whole scene
            var center = new THREE.Vector3(0,0,0);
            var radiuses = new Array();
            var positions = new Array();
            // compute center of all objects
            scene.traverse(function(child) {
                if (child instanceof THREE.Mesh) {
                    child.geometry.computeBoundingBox();
                    var box = child.geometry.boundingBox;
                    var curCenter = new THREE.Vector3().copy(box.min).add(box.max).multiplyScalar(0.5);
                    var radius = new THREE.Vector3().copy(box.max).distanceTo(box.min)/2.;
                    center.add(curCenter);
                    positions.push(curCenter);
                    radiuses.push(radius);
                }
            });
            if (radiuses.length > 0) {
                center.divideScalar(radiuses.length*0.7);
            }
            var maxRad = 1.;
            // compute bounding radius
            for (var ichild = 0; ichild < radiuses.length; ++ichild) {
                var distToCenter = positions[ichild].distanceTo(center);
                var totalDist = distToCenter + radiuses[ichild];
                if (totalDist > maxRad) {
                    maxRad = totalDist;
                }
            }
            maxRad = maxRad * 0.7; // otherwise the scene seems to be too far away
            camera.lookAt(center);
            var direction = new THREE.Vector3().copy(camera.position).sub(controls.target);
            var len = direction.length();
            direction.normalize();
            // compute new distance of camera to middle of scene to fit the object to screen
            var lnew = maxRad / Math.sin(camera.fov/180. * Math.PI / 2.);
            direction.multiplyScalar(lnew);
            var pnew = new THREE.Vector3().copy(center).add(direction);
            // change near far values to avoid culling of objects
            camera.position.set(pnew.x, pnew.y, pnew.z);
            camera.far = lnew*50;
            camera.near = lnew*50*0.001;
            camera.updateProjectionMatrix();
            controls.target = center;
            controls.update();
            // adds and adjust a grid helper if needed
            gridHelper = new THREE.GridHelper(maxRad*4, 10)
            scene.add(gridHelper);
            gridHelper.visible = false;
            // axisHelper
            axisHelper = new THREE.AxesHelper(maxRad);
            scene.add(axisHelper);
            axisHelper.visible = false
        }
        function render() {
            //@IncrementTime@  TODO UNCOMMENT
            update_lights();
            renderer.render(scene, camera);
        }
    </script>
</body>
"""


class Viewer(threejs_renderer.ThreejsRenderer):
    """Extension of pythonOCC's ThreeJS renderer with some tweaks."""
    # NB: The code below is mostly copied from ThreejsRenderer, with a few
    # changes to improve the display. The original style hasn't been changed,
    # so it looks a bit different from the rest of my code.
    def DisplayShape(self,
                     shape,
                     export_edges=False,
                     color=(0.65, 0.65, 0.7),
                     specular_color=(0.2, 0.2, 0.2),
                     shininess=0.9,
                     transparency=0.,
                     line_color=(0, 0., 0.),
                     line_width=1.,
                     mesh_quality=1.):
        # if the shape is an edge or a wire, use the related functions
        if is_edge(shape):
            print("discretize an edge")
            pnts = discretize_edge(shape, deflection=1e-2)
            edge_hash = "edg%s" % uuid.uuid4().hex
            str_to_write = export_edgedata_to_json(edge_hash, pnts)
            edge_full_path = os.path.join(self._path, edge_hash + '.json')
            with open(edge_full_path, "w") as edge_file:
                edge_file.write(str_to_write)
            # store this edge hash
            self._3js_edges[edge_hash] = [color, line_width]
            return self._3js_shapes, self._3js_edges
        elif is_wire(shape):
            print("discretize a wire")
            pnts = discretize_wire(shape)
            wire_hash = "wir%s" % uuid.uuid4().hex
            str_to_write = export_edgedata_to_json(wire_hash, pnts)
            wire_full_path = os.path.join(self._path, wire_hash + '.json')
            with open(wire_full_path, "w") as wire_file:
                wire_file.write(str_to_write)
            # store this edge hash
            self._3js_edges[wire_hash] = [color, line_width]
            return self._3js_shapes, self._3js_edges
        shape_uuid = uuid.uuid4().hex
        shape_hash = "shp%s" % shape_uuid
        # tesselate
        tess = ShapeTesselator(shape)
        tess.Compute(compute_edges=export_edges,
                     mesh_quality=mesh_quality,
                     parallel=True)
        # update spinning cursor
        sys.stdout.write("\r%s mesh shape %s, %i triangles     " % (next(self.spinning_cursor),
                                                                    shape_hash,
                                                                    tess.ObjGetTriangleCount()))
        sys.stdout.flush()
        # export to 3JS
        shape_full_path = os.path.join(self._path, shape_hash + '.json')
        # add this shape to the shape dict, sotres everything related to it
        self._3js_shapes[shape_hash] = [export_edges, color, specular_color, shininess, transparency, line_color, line_width]
        # generate the mesh
        #tess.ExportShapeToThreejs(shape_hash, shape_full_path)
        # and also to JSON
        with open(shape_full_path, 'w') as json_file:
            json_file.write(tess.ExportShapeToThreejsJSONString(shape_uuid))
        # draw edges if necessary
        if export_edges:
            # export each edge to a single json
            # get number of edges
            nbr_edges = tess.ObjGetEdgeCount()
            for i_edge in range(nbr_edges):
                # after that, the file can be appended
                str_to_write = ''
                edge_point_set = []
                nbr_vertices = tess.ObjEdgeGetVertexCount(i_edge)
                for i_vert in range(nbr_vertices):
                    edge_point_set.append(tess.GetEdgeVertex(i_edge, i_vert))
                # write to file
                edge_hash = "edg%s" % uuid.uuid4().hex
                str_to_write += export_edgedata_to_json(edge_hash, edge_point_set)
                # create the file
                edge_full_path = os.path.join(self._path, edge_hash + '.json')
                with open(edge_full_path, "w") as edge_file:
                    edge_file.write(str_to_write)
                # store this edge hash, with black color
                self._3js_edges[edge_hash] = [(0, 0, 0), line_width]
        return self._3js_shapes, self._3js_edges
