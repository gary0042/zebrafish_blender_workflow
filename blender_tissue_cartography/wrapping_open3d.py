# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03b_wrapping_open3d.ipynb.

# %% auto 0
__all__ = ['shrinkwrap_o3d']

# %% ../nbs/03b_wrapping_open3d.ipynb 1
from . import io as tcio
from . import registration as tcreg
from . import interface_open3d as into3d
import numpy as np
from copy import deepcopy
import open3d as o3d

# %% ../nbs/03b_wrapping_open3d.ipynb 29
def shrinkwrap_o3d(mesh_source, mesh_target, n_iter_smooth_target=1, n_iter_smooth_wrapped=1):
    """
    Shrink-wrap the source mesh onto the target mesh using open3d.
    
    Sets the vertex positions of mesh_source to the closes point on the surface of mesh_target (not necessarily
    a vertex). Optionally, smoothes the target mesh and the wrapped mesh for smoother results using a
    simple smoothing filter filter (recommended). Gives out a warning if the shrink-wrapping flips
    any vertex normals, which can indicate problems.
    
    The shrinkwrapped mesh still has the UV maps of the source mesh, and so can be used to compute
    cartographic projections.
    
    Parameters
    ----------
    mesh_source : tcio.ObjMesh
        Mesh to be deformed
    mesh_target : tcio.ObjMesh
        Mesh with target shape
    n_iter_smooth_target : int, default 1
        Smoothing iterations for target. Setting this value too high will result in "shrinkage",
        and the mesh won't match your image data well anymore.
    n_iter_smooth_wrapped : int, default 1
        Smoothing iterations for shrinkwrapped mesh, after shrinkwrapping. Setting this value
        too high will result in "shrinkage",  and the mesh won't match your image data well anymore.

    Returns
    -------
    mesh_wrapped : tcio.ObjMesh

    """
    mesh_target_o3d = into3d.convert_to_open3d(mesh_target)
    mesh_source_o3d = into3d.convert_to_open3d(mesh_source)
    mesh_source_wrapped_o3d = deepcopy(mesh_source_o3d)
    # smooth - have to convert to `legacy` representation
    mesh_target_o3d = o3d.t.geometry.TriangleMesh.from_legacy(
        mesh_target_o3d.to_legacy().filter_smooth_simple(number_of_iterations=n_iter_smooth_target))
    # create a raycasting scene and compute the closest point on the surface of the target mesh.
    scene = o3d.t.geometry.RaycastingScene()
    _ = scene.add_triangles(mesh_target_o3d)
    query_points = mesh_source_o3d.vertex.positions.numpy()
    closest_points = scene.compute_closest_points(o3d.core.Tensor(query_points,
                                                                  dtype=o3d.core.Dtype.Float32))["points"]
    # wrap mesh by setting vertex positions to closes ones on the target mesh
    mesh_source_wrapped_o3d.vertex.positions = closest_points
    mesh_source_wrapped_o3d.compute_vertex_normals()
    mesh_source_wrapped_o3d = mesh_source_wrapped_o3d.to_legacy()
    mesh_source_wrapped_filtered_o3d = mesh_source_wrapped_o3d.filter_smooth_simple(
        number_of_iterations=n_iter_smooth_wrapped)
    mesh_source_wrapped_filtered_o3d.triangle_uvs = mesh_source_wrapped_o3d.triangle_uvs
    mesh_wrapped = into3d.convert_from_open3d(mesh_source_wrapped_filtered_o3d)
    # check if any normals were flipped
    dots = np.einsum("vi,vi->v", mesh_source.vertex_normals, mesh_wrapped.vertex_normals)
    if np.sum(dots < 0) > 0:
        warnings.warn(f"Warning: {np.sum(dots<0)} normal(s) flipped during shrink-wrapping")
    return mesh_wrapped
