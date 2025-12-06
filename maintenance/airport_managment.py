from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, UpdateView, CreateView, ListView
from .forms import AirportForm
from .models import Airport


class AirportCreateView(LoginRequiredMixin, CreateView):
    model = Airport
    form_class = AirportForm
    template_name = 'maintenance/airport/airport_form.html'
    success_url = reverse_lazy('airport_list')

    def form_valid(self, form):
        # Your existing processing...
        response = super().form_valid(form)
        messages.success(self.request, f'Airport successfully Added.')
        return response

    def get_success_url(self):
        return self.success_url


# View for listing Airport
class AirportListView(LoginRequiredMixin, ListView):
    model = Airport
    context_object_name = 'airports'
    template_name = 'maintenance/airport/airport_list.html'
    paginate_by = 50  # Default value

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('name')  # odering the queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_pagination = self.request.GET.get('paginate_by', self.paginate_by)
        paginator = Paginator(self.get_queryset(), user_pagination)
        page = self.request.GET.get('page')

        try:
            airports = paginator.page(page)
        except PageNotAnInteger:
            airports = paginator.page(1)
        except EmptyPage:
            airports = paginator.page(paginator.num_pages)

        context['airports'] = airports
        return context


# View for updating Airport
class AirportUpdateView(LoginRequiredMixin, UpdateView):
    model = Airport
    form_class = AirportForm
    template_name = 'maintenance/airport/airport_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add your success message here
        messages.success(self.request, 'Airport details have been updated successfully.')
        return response

    def get_success_url(self):
        # This method redirects to the 'airport_list' URL after successful form submission
        return reverse_lazy('airport_list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AirportUpdateView, self).dispatch(*args, **kwargs)


class AirportDetailView(LoginRequiredMixin, DetailView):
    model = Airport
    context_object_name = 'airport'
    template_name = 'maintenance/airport/airport_detail.html'
