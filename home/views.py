from django.shortcuts import render

def lionsol_homepage(request):
    """View for the Lionsol homepage"""
    return render(request, 'home/lionsol_homepage.html')
