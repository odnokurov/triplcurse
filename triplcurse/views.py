from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

def home(request):
    return render(request, 'home.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('user_profile')
        else:
            messages.error(request, "Неверный логин или пароль.")
    return render(request, 'login.html')

def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Регистрация прошла успешно. Вы можете войти.")
            return redirect('login')
        else:
            pass
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def create_application(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        errors = []

        if not title or not description or not category_id or not image:
            errors.append("Все поля обязательны.")

        if image:
            if image.size > 2 * 1024 * 1024:
                errors.append("Размер файла не должен превышать 2 МБ.")
            ext = image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'bmp']:
                errors.append("Недопустимый формат файла. Разрешены: jpg, jpeg, png, bmp.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            try:
                category = Category.objects.get(id=category_id)
                Application.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    category=category,
                    image=image,
                    status='new'
                )
                messages.success(request, "Заявка успешно создана.")
                return redirect('user_applications')
            except Category.DoesNotExist:
                messages.error(request, "Выбрана некорректная категория.")

    return render(request, 'create_application.html', {'categories': categories})

@login_required
def user_applications(request):
    status_filter = request.GET.get('status')
    applications = Application.objects.filter(user=request.user).order_by('-created_at')

    if status_filter in ['new', 'in_progress', 'completed']:
        applications = applications.filter(status=status_filter)

    return render(request, 'user_applications.html', {
        'applications': applications,
        'status_filter': status_filter
    })

@login_required
def delete_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)


    if app.status != 'new':
        messages.error(request, "Можно удалять только заявки со статусом «Новая».")
        return redirect('user_applications')

    if request.method == 'POST':
        app.delete()
        messages.success(request, "Заявка удалена.")
        return redirect('user_applications')

    return render(request, 'confirm_delete.html', {'application': app})