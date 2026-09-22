import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .forms import (
    RegisterForm, LoginForm, UserUpdateForm, ProfileUpdateForm,
    CustomPasswordChangeForm, ForgotPasswordForm, VerifyOTPForm, SetNewPasswordForm
)
from .models import UserProfile, PasswordResetOTP


def send_otp_email(user, otp_code):
    """Send OTP code to user's email via SMTP."""
    subject = 'Your Password Reset OTP & Account Details - DocIntel'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'DocIntel <noreply@docintel.com>')
    to_email = user.email

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 20px; }}
            .email-card {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 36px 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #e5eaf1; }}
            .brand {{ font-size: 22px; font-weight: 800; color: #2563eb; text-align: center; margin-bottom: 24px; text-transform: uppercase; letter-spacing: 1px; }}
            .title {{ font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 12px; text-align: center; }}
            .text {{ font-size: 15px; color: #475569; line-height: 1.6; text-align: center; margin-bottom: 20px; }}
            .info-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; margin: 16px 0; text-align: center; font-size: 15px; color: #1e293b; }}
            .otp-box {{ background: linear-gradient(135deg, #eff6ff, #e0e7ff); border: 2px dashed #3b82f6; border-radius: 12px; padding: 18px; text-align: center; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; margin: 20px 0; }}
            .footer {{ font-size: 13px; color: #94a3b8; text-align: center; margin-top: 28px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
        </style>
    </head>
    <body>
        <div class="email-card">
            <div class="brand">📄 DocIntel</div>
            <div class="title">Password Reset Verification</div>
            <p class="text">Hello <strong>{user.first_name or user.username}</strong>,</p>
            <div class="info-box">
                👤 Your Registered Username: <strong style="color: #2563eb;">{user.username}</strong>
            </div>
            <p class="text">You requested to reset your password. Use the OTP code below to proceed:</p>
            <div class="otp-box">{otp_code}</div>
            <p class="text" style="font-size: 13px; color: #ef4444;">⏱️ This code is valid for <strong>10 minutes</strong>. Do not share this OTP with anyone.</p>
            <div class="footer">If you did not request a password reset, please ignore this email.<br>&copy; DocIntel AI Platform</div>
        </div>
    </body>
    </html>
    """
    text_content = f"Hello {user.first_name or user.username},\n\nYour registered username is: {user.username}\nYour OTP for password reset is: {otp_code}\nThis OTP is valid for 10 minutes.\n\nIf you did not request this, please ignore this email."

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def send_welcome_email(user):
    """Send Welcome email upon user registration via SMTP."""
    if not user.email:
        return

    subject = 'Welcome to DocIntel - Account Created Successfully! 🎉'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'DocIntel <noreply@docintel.com>')
    to_email = user.email

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 20px; }}
            .email-card {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 18px; padding: 38px 34px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #e5eaf1; }}
            .brand {{ font-size: 24px; font-weight: 800; color: #2563eb; text-align: center; margin-bottom: 24px; text-transform: uppercase; letter-spacing: 1px; }}
            .title {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 14px; text-align: center; }}
            .text {{ font-size: 15px; color: #475569; line-height: 1.6; text-align: center; margin-bottom: 20px; }}
            .info-box {{ background: linear-gradient(135deg, #eff6ff, #f0fdf4); border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px; margin: 20px 0; text-align: left; font-size: 14.5px; color: #1e293b; line-height: 1.8; }}
            .footer {{ font-size: 13px; color: #94a3b8; text-align: center; margin-top: 28px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
        </style>
    </head>
    <body>
        <div class="email-card">
            <div class="brand">📄 DocIntel</div>
            <div class="title">Welcome aboard, {user.first_name or user.username}! 👋</div>
            <p class="text">Thank you for creating an account on <strong>DocIntel AI Platform</strong>. Your account has been set up successfully!</p>
            <div class="info-box">
                📌 <strong>Your Account Details:</strong><br>
                👤 <strong>Username:</strong> {user.username}<br>
                ✉️ <strong>Email Address:</strong> {user.email}
            </div>
            <p class="text">You can now upload documents, generate AI summaries, extract insights, and chat with your files effortlessly.</p>
            <div class="footer">&copy; DocIntel AI Platform • All rights reserved</div>
        </div>
    </body>
    </html>
    """
    text_content = f"Hello {user.first_name or user.username},\n\nWelcome to DocIntel! Your account has been created successfully.\n\nYour Account Details:\nUsername: {user.username}\nEmail: {user.email}\n\nHappy analyzing!\nDocIntel Team"

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)
    except Exception:
        pass


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            send_welcome_email(user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created and a welcome email has been sent.')
            return redirect('dashboard:index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})



def login_view(request):
    """Handle user login - supports logging in with username OR email."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        post_data = request.POST.copy()
        username_or_email = post_data.get('username', '').strip()

        # If user entered an email address instead of username, resolve to actual username
        if '@' in username_or_email:
            matched_user = User.objects.filter(email__iexact=username_or_email).first()
            if matched_user:
                post_data['username'] = matched_user.username

        form = LoginForm(request, data=post_data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})



def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing:home')


@login_required
def profile_view(request):
    """Display user profile."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    documents = request.user.documents.all().order_by('-uploaded_at')[:5]
    context = {
        'profile': profile,
        'recent_documents': documents,
        'total_documents': request.user.documents.count(),
        'total_questions': request.user.chat_messages.filter(role='user').count(),
        'total_summaries': request.user.documents.filter(summaries__isnull=False).distinct().count(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """Handle profile editing."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def change_password_view(request):
    """Handle password change."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


def forgot_password_view(request):
    """Handle forgot password - send OTP via SMTP."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip()
            user = User.objects.filter(email__iexact=email).first()
            if user:
                otp_code = f"{random.randint(100000, 999999)}"
                PasswordResetOTP.objects.create(user=user, otp_code=otp_code)

                try:
                    send_otp_email(user, otp_code)
                    request.session['reset_user_id'] = user.id
                    messages.success(request, f'Verification OTP has been sent to {user.email}. Please check your inbox.')
                    return redirect('accounts:verify_otp')
                except Exception as e:
                    messages.error(request, f'Failed to send OTP email: {str(e)}')
            else:
                messages.error(request, 'No account found with that email address.')
        else:
            messages.error(request, 'Please enter a valid email address.')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


def verify_otp_view(request):
    """Verify 6-digit OTP code entered by user."""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please enter your email again.')
        return redirect('accounts:forgot_password')

    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'User account not found.')
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code'].strip()
            otp_record = PasswordResetOTP.objects.filter(
                user=user,
                otp_code=otp_code,
                is_used=False
            ).order_by('-created_at').first()

            if otp_record and otp_record.is_valid():
                otp_record.is_verified = True
                otp_record.save()
                request.session['otp_verified'] = True
                request.session['verified_otp_id'] = otp_record.id
                messages.success(request, 'OTP verified successfully! Please enter your new password.')
                return redirect('accounts:reset_password')
            else:
                messages.error(request, 'Invalid or expired OTP. Please check the code or click Resend OTP.')
        else:
            messages.error(request, 'Please enter a valid 6-digit OTP code.')
    else:
        form = VerifyOTPForm()

    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'user_email': user.email
    })


def resend_otp_view(request):
    """Resend OTP code to user's email."""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please start forgot password again.')
        return redirect('accounts:forgot_password')

    user = User.objects.filter(id=user_id).first()
    if user:
        otp_code = f"{random.randint(100000, 999999)}"
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code)
        try:
            send_otp_email(user, otp_code)
            messages.success(request, f'New OTP code sent to {user.email}.')
        except Exception as e:
            messages.error(request, f'Failed to resend OTP email: {str(e)}')

    return redirect('accounts:verify_otp')


def reset_password_view(request):
    """Allow user to set a new password after successful OTP verification."""
    user_id = request.session.get('reset_user_id')
    otp_verified = request.session.get('otp_verified')

    if not user_id or not otp_verified:
        messages.error(request, 'Unauthorized access. Please verify your OTP first.')
        return redirect('accounts:forgot_password')

    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'User account not found.')
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()

            verified_otp_id = request.session.get('verified_otp_id')
            if verified_otp_id:
                PasswordResetOTP.objects.filter(id=verified_otp_id).update(is_used=True)

            request.session.pop('reset_user_id', None)
            request.session.pop('otp_verified', None)
            request.session.pop('verified_otp_id', None)

            messages.success(request, 'Your password has been reset successfully! Please sign in with your new password.')
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = SetNewPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form})


@login_required
def update_settings(request):
    """Update user settings via AJAX."""
    if request.method == 'POST':
        profile = request.user.profile
        theme = request.POST.get('theme')
        language = request.POST.get('language')
        notifications = request.POST.get('notifications')

        if theme:
            profile.theme_preference = theme
        if language:
            profile.language = language
        if notifications is not None:
            profile.email_notifications = notifications == 'true'

        profile.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

