import logging
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views import View

from .forms import ChangePasswordForm, ProfileUpdateForm, UserLoginForm, UserRegistrationForm
from .models import CustomUser, LoginHistory

logger = logging.getLogger(__name__)


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR'))


def dashboard_for(user):
    if user.is_superuser:
        return 'dashboard:super_admin'
    if user.role == CustomUser.Role.ADMIN:
        return 'dashboard:admin_dashboard'
    if user.role == CustomUser.Role.SCORER:
        return 'dashboard:scorer'
    return 'dashboard:home'


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(dashboard_for(request.user))
        return render(request, self.template_name, {'form': UserRegistrationForm()})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        messages.success(request, 'Account created successfully. You can now sign in.')
        return redirect('accounts:login')


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(dashboard_for(request.user))
        return render(request, self.template_name, {'form': UserLoginForm(request=request)})

    def post(self, request):
        form = UserLoginForm(request=request, data=request.POST)
        if not form.is_valid():
            identifier = request.POST.get('username', '')
            user = CustomUser.objects.filter(email__iexact=identifier).first() or CustomUser.objects.filter(
                username__iexact=identifier
            ).first()
            if user:
                LoginHistory.objects.create(
                    user=user, successful=False, ip_address=client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                )
            return render(request, self.template_name, {'form': form})
        user = form.get_user()
        login(request, user, backend='apps.accounts.backends.EmailOrUsernameBackend')
        request.session.set_expiry(2592000 if form.cleaned_data.get('remember_me') else 0)
        user.last_login_ip = client_ip(request)
        user.last_login_user_agent = request.META.get('HTTP_USER_AGENT', '')[:512]
        user.save(update_fields=['last_login', 'last_login_ip', 'last_login_user_agent', 'updated_at'])
        LoginHistory.objects.create(
            user=user, successful=True, ip_address=client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
        messages.success(request, f'Welcome back, {user.get_short_name()}!')
        return redirect(request.POST.get('next') or request.GET.get('next') or dashboard_for(user))


class LogoutView(View):
    @method_decorator(csrf_protect)
    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('home')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': ProfileUpdateForm(instance=request.user),
            'pwd_form': ChangePasswordForm(user=request.user),
        })

    def post(self, request):
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile details updated successfully.')
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form, 'pwd_form': ChangePasswordForm(user=request.user)})


class ChangePasswordView(LoginRequiredMixin, View):
    def post(self, request):
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('accounts:profile')
        return render(request, 'accounts/profile.html', {
            'form': ProfileUpdateForm(instance=request.user), 'pwd_form': form,
        })
