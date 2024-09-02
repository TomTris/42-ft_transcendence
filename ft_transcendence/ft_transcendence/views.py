from django.shortcuts import render, redirect, get_object_or_404

def loop_detect_view(request):
    return render(request, "loop_detect.html")