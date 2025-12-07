from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Application, Category
from .forms import UserRegistrationForm
from django.contrib.auth.models import User

def home(request):
    completed_applications = Application.objects.filter(
        status='completed'
    ).order_by('-created_at')[:4]

    in_progress_count = Application.objects.filter(status='in_progress').count()

    return render(request, 'triplcurse/home.html', {
        'completed_applications': completed_applications,
        'in_progress_count': in_progress_count,
    })

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
    return render(request, 'triplcurse/login.html')

def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            user.first_name = form.cleaned_data['full_name']
            user.save()
            messages.success(request, "Регистрация прошла успешно. Теперь вы можете войти.")
            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'triplcurse/register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def create_application(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        errors = []

        if not title:
            errors.append("Поле «Название» обязательно.")
        if not description:
            errors.append("Поле «Описание» обязательно.")
        if not category_id:
            errors.append("Выберите категорию.")
        if not image:
            errors.append("Прикрепите изображение (план или фото помещения).")

        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                errors.append("Выбрана некорректная категория.")

        if image:
            if image.size > 2 * 1024 * 1024:
                errors.append("Размер изображения не должен превышать 2 МБ.")
            ext = image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'bmp']:
                errors.append("Разрешены только форматы: jpg, jpeg, png, bmp.")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            Application.objects.create(
                user=request.user,
                title=title,
                description=description,
                category=category,
                image=image,
                status='new'
            )
            messages.success(request, "Заявка успешно создана!")
            return redirect('user_profile')  # или 'user_applications'

    return render(request, 'triplcurse/create_application.html', {
        'categories': categories
    })

@login_required
def user_applications(request):
    status_filter = request.GET.get('status')
    applications = Application.objects.filter(user=request.user).order_by('-created_at')

    if status_filter in ['new', 'in_progress', 'completed']:
        applications = applications.filter(status=status_filter)

    return render(request, 'triplcurse/user_profile.html', {
        'applications': applications,
        'status_filter': status_filter
    })

@login_required
def delete_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)


    if app.status != 'new':
        messages.error(request, "Можно удалять только заявки со статусом «Новая».")
        return redirect('user_profile')

    if request.method == 'POST':
        app.delete()
        messages.success(request, "Заявка удалена.")
        return redirect('user_profile')

    return render(request, 'triplcurse/user_profile.html', {'application': app})

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    status_filter = request.GET.get('status')
    applications = Application.objects.all().order_by('-created_at')
    if status_filter in ['new', 'in_progress', 'completed']:
        applications = applications.filter(status=status_filter)

    categories = Category.objects.all()
    return render(request, 'triplcurse/admin_dashboard.html', {
        'applications': applications,
        'categories': categories,
        'status_filter': status_filter,
    })

@user_passes_test(is_admin)
def update_application_status(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if app.status != 'new':
        messages.error(request, "Статус можно изменить только у заявок со статусом «Новая».")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        status = request.POST.get('status')
        if status == 'in_progress':
            comment = request.POST.get('admin_comment', '').strip()
            if not comment:
                messages.error(request, "Комментарий обязателен.")
                return redirect('admin_dashboard')
            app.status = 'in_progress'
            app.admin_comment = comment
        elif status == 'completed':
            design_image = request.FILES.get('design_image')
            if not design_image:
                messages.error(request, "Изображение дизайна обязательно.")
                return redirect('admin_dashboard')
            if design_image.size > 2 * 1024 * 1024:
                messages.error(request, "Размер изображения не должен превышать 2 МБ.")
                return redirect('admin_dashboard')
            ext = design_image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'bmp']:
                messages.error(request, "Недопустимый формат изображения.")
                return redirect('admin_dashboard')
            app.status = 'completed'
            app.design_image = design_image
        else:
            messages.error(request, "Недопустимый статус.")
            return redirect('admin_dashboard')
        app.save()
        messages.success(request, "Статус заявки обновлён.")
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name and not Category.objects.filter(name=name).exists():
            Category.objects.create(name=name)
            messages.success(request, f"Категория «{name}» добавлена.")
        else:
            messages.error(request, "Категория с таким названием уже существует или пустая.")
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def delete_category(request, cat_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=cat_id)
        category.delete()
        messages.success(request, f"Категория и все её заявки удалены.")
    return redirect('admin_dashboard')

@login_required
def user_profile(request):
    status_filter = request.GET.get('status')
    applications = Application.objects.filter(user=request.user).order_by('-created_at')

    if status_filter in ['new', 'in_progress', 'completed']:
        applications = applications.filter(status=status_filter)

    return render(request, 'triplcurse/user_profile.html', {
        'applications': applications,
        'status_filter': status_filter
    })