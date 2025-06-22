from django.shortcuts import render

# Create your views here.

def index(request):
    """
    Отображает главную страницу для скачивания приложения.
    """
    return render(request, 'mainpage/index.html')
