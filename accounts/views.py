from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.contrib import messages
from django.db.models import Q
from .forms import CustomUserChangeForm, CustomUserCreationForm, CustomPasswordResetForm
from .models import CustomUser
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def login(request):
    return render(request, 'accounts/login.html', {'title': 'Entebbe Airways'})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, f'Your Profile has been updated and Logged!')
            return redirect('profile')
    else:
        u_form = CustomUserChangeForm(instance=request.user)

    context = {
        'u_form': u_form,
    }

    return render(request, 'accounts/users_profile.html', context)



class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'accounts/users_list.html'
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        query = self.request.GET.get('q')

        if query:
            return CustomUser.objects.filter(
                Q(email__icontains=query) |
                Q(employee_id__icontains=query) |
                Q(department__icontains=query) |
                Q(contact_number__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(username__icontains=query)
            )

        return super().get_queryset()


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'accounts/users_update.html'
    fields = ['first_name','last_name','username','email', 'employee_id', 'department', 'designation', 'contact_number', 'address', 'date_of_birth',
              'update_comments', 'image']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter the queryset to only include the current user
        return queryset.filter(pk=self.kwargs['pk'])

    def get_initial(self):
        initial = super().get_initial()
        initial['update_comments'] = ''  # Set the update_comments field to an empty value
        return initial

    def form_valid(self, form):
        form.instance.updated_date = timezone.now()
        form.instance.updated_by = self.request.user.username

        update_comments = form.cleaned_data['update_comments']
        if not update_comments:
            form.add_error('update_comments', 'Update comments are required.')
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'User Updated Successfully and Logged.')
        return reverse('user_detail', kwargs={'pk': self.object.pk})


class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/users_details.html'
    context_object_name = 'user'


class UserCreateView(LoginRequiredMixin, CreateView):
    model = CustomUser
    template_name = 'accounts/users_register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        # Save the user without committing to the database
        user = form.save(commit=False)
        # Set the password manually
        password = form.cleaned_data['password2']
        user.set_password(password)
        # Save the user to the database
        user.save()
        return super().form_valid(form)


@login_required
def reset_password(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            # Update admin_password_reset field with username and timestamp
            user.admin_password_reset = f'{request.user.username} ({timezone.now()})'
            user.save()
            messages.success(request, 'Password Changed Successfully and Logged')
            return redirect('user_detail', pk=user.id)
        else:
            messages.error(request, 'Passwords do not match')

    else:
        form = CustomPasswordResetForm()

    return render(request, 'accounts/users_admin_preset.html', {'form': form, 'user': user})
