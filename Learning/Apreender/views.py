from django.shortcuts import render
from django.http import HttpResponse



def index(request):
    #return index page
    
    return render(request, 'Apreender/index.html')
