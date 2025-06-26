from django.shortcuts import render, get_object_or_404
from reconstruction.models import Reconstruction

# Create your views here.

def mesh_view(request, id):
    reconstruction = get_object_or_404(Reconstruction, id=id)
    mesh_url = f"/media/{reconstruction.mesh_file_path}"
    return render(request, 'mesh_render/mesh_view.html', {'id': id, 'mesh_url': mesh_url})
