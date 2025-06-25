from django.shortcuts import render
from .models import ApplicationFile
from urllib.parse import urljoin
from core import config

# Create your views here.

def index(request):
    """
    Отображает главную страницу для скачивания приложения.
    """
    app_file = ApplicationFile.objects.filter(os=ApplicationFile.OS.ANDROID, hidden=False).order_by('-uploaded_at').first()
    download_url = None
    version = None
    if app_file and app_file.file:
        base = getattr(config, 'APPLICATION_URL', '')
        media_url = '/media/'
        download_url = urljoin(urljoin(base, media_url), app_file.file.name)
        version = app_file.version
    return render(request, 'mainpage/index.html', {'download_url': download_url, 'version': version})
