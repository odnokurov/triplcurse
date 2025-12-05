from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Application, Category

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

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard(request):
    status_filter = request.GET.get('status')
    applications = Application.objects.all().order_by('-created_at')
    if status_filter in ['new', 'in_progress', 'completed']:
        applications = applications.filter(status=status_filter)

    categories = Category.objects.all()
    return render(request, 'admin_dashboard.html', {
        'applications': applications,
        'categories': categories,
        'status_filter': status_filter
    })

@user_passes_test(is_admin)
def update_application_status(request, app_id):
    app = get_object_or_404(Application, id=app_id)

    if app.status != 'new':
        messages.error(request, "Статус можно изменить только у заявок со статусом «Новая».")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status == 'in_progress':
            comment = request.POST.get('admin_comment', '').strip()
            if not comment:
                messages.error(request, "Комментарий обязателен при смене статуса на «Принято в работу».")
                return redirect('admin_dashboard')
            app.status = 'in_progress'
            app.admin_comment = comment

        elif new_status == 'completed':
            design_image = request.FILES.get('design_image')
            if not design_image:
                messages.error(request, "Изображение дизайна обязательно при смене статуса на «Выполнено».")
                return redirect('admin_dashboard')

            # Валидация изображения
            ext = design_image.name.split('.')[-1].lower()
            size = design_image.size
            if ext not in ['jpg', 'jpeg', 'png', 'bmp']:
                messages.error(request, "Недопустимый формат изображения дизайна. Разрешены: jpg, jpeg, png, bmp.")
                return redirect('admin_dashboard')
            if size > 2 * 1024 * 1024:
                messages.error(request, "Размер изображения дизайна не должен превышать 2 МБ.")
                return redirect('admin_dashboard')

            app.status = 'completed'
            app.design_image = design_image

        else:
            messages.error(request, "Недопустимый статус.")
            return redirect('admin_dashboard')

        app.save()
        messages.success(request, f"Статус заявки «{app.title}» обновлён.")
        return redirect('admin_dashboard')

    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def manage_categories(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            if name:
                if Category.objects.filter(name=name).exists():
                    messages.error(request, "Категория с таким названием уже существует.")
                else:
                    Category.objects.create(name=name)
                    messages.success(request, "Категория добавлена.")
            else:
                messages.error(request, "Название категории не может быть пустым.")

        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            try:
                category = Category.objects.get(id=cat_id)
                category.delete()  # CASCADE удалит все заявки этой категории
                messages.success(request, f"Категория «{category.name}» и все её заявки удалены.")
            except Category.DoesNotExist:
                messages.error(request, "Категория не найдена.")

        return redirect('admin_dashboard')

    return redirect('admin_dashboard')