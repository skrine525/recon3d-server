from django.shortcuts import render, get_object_or_404
from reconstruction.models import Reconstruction
import json

# Create your views here.

def mesh_view(request, id):
    reconstruction = get_object_or_404(Reconstruction, id=id)
    mesh_url = f"/media/{reconstruction.mesh_file_path}"
    
    # Считываем координаты из query-параметров
    try:
        x = float(request.GET.get('x'))
        y = float(request.GET.get('y'))
        z = float(request.GET.get('z'))
        target_point = {'x': x, 'y': y, 'z': z}
    except (TypeError, ValueError):
        target_point = None

    context = {
        'id': id,
        'mesh_url': mesh_url,
        'target_point_json': json.dumps(target_point)
    }
    return render(request, 'mesh_render/mesh_view.html', context)
