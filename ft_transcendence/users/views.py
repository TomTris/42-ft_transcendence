from django.shortcuts import render, redirect
from .admin import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def login_view(request):
    logout(request)
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'redirect': 'home'})  # Response for AJAX requests
                else:
                    return redirect('home')  # Response for normal form submissions
            else:
                # Invalid credentials
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Invalid username or password'}, status=400)
                else:
                    form.add_error(None, 'Invalid username or password')
        else:
            # Form is not valid
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Form is not valid'}, status=400)
            else:
                form.add_error(None, 'Form is not valid')
    else:
        form = AuthenticationForm()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'partials/login.html', {'form': form})  # Partial template for AJAX requests
    return render(request, 'login.html', {'form': form})

@csrf_exempt
def register_view(request):
    logout(request)
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form":form})