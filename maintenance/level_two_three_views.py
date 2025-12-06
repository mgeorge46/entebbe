from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django_tables2 import RequestConfig
from django.views.generic import ListView, DetailView, UpdateView, TemplateView
# from django.views.generic.detail import DetailView

from .forms import AircraftSub2ComponentForm, AircraftSub3ComponentForm
from .models import Aircraft, AircraftSubComponent, AircraftSub2Component, AircraftSub3Component
from .tables import Sub2ComponentTable, Sub3ComponentTable


@login_required
def add_aircraft_sub2_component(request, sub_component_id):
    sub_component = get_object_or_404(AircraftSubComponent, pk=sub_component_id)
    aircraft = sub_component.parent_component.aircraft_attached

    if request.method == 'POST':
        form = AircraftSub2ComponentForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('multiple_entries'):
                serial_numbers = form.cleaned_data[
                    'serial_numbers']  # Assuming this is already a list or cleaned to be a list
                num_created = 0
                with transaction.atomic():
                    for serial_number in serial_numbers:
                        sub2_component = AircraftSub2Component()
                        for field in form.cleaned_data:
                            if field not in ['multiple_entries', 'serial_numbers']:
                                setattr(sub2_component, field, form.cleaned_data[field])
                        sub2_component.parent_sub_component = sub_component
                        sub2_component.added_by = request.user
                        sub2_component.serial_number = serial_number.strip()  # Clean serial number
                        sub2_component.save()
                        num_created += 1
                messages.success(request, f'{num_created} Second Level Components Added Successfully')
            else:
                sub2_component = form.save(commit=False)
                sub2_component.parent_sub_component = sub_component
                sub2_component.added_by = request.user
                sub2_component.save()
                messages.success(request, 'Second Level Component Added Successfully')
            return redirect('aircraft_sub2_components_list', pk=sub_component.id)
    else:
        form = AircraftSub2ComponentForm()

    return render(request, 'maintenance/sub2_component/sub2_component_add.html',
                  {'form': form, 'sub_component': sub_component, 'aircraft': aircraft})


class Sub2ComponentListView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/sub2_component/sub2_component_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_term = self.request.GET.get('search', '')
        min_hours = int(self.request.GET.get('min_hours', '0')) if self.request.GET.get('min_hours') else None
        max_hours = int(self.request.GET.get('max_hours', '0')) if self.request.GET.get('max_hours') else None
        sub_component_id = self.kwargs['pk']
        sub_component = get_object_or_404(AircraftSubComponent, pk=sub_component_id)

        # Only get subcomponents of the given main component
        sub2_components = AircraftSub2Component.objects.filter(parent_sub_component=sub_component)
        total_sub2_components = sub2_components.count()

        search_fields = [
            'component_name',
            'parent_sub_component__component_name',
            'parent_sub_component__parent_component__aircraft_attached__abbreviation'
        ]

        query = Q()
        for field in search_fields:
            query |= Q(**{f'{field}__icontains': search_term})

        sub2_components = sub2_components.filter(
            query
        )

        if min_hours is not None:
            sub2_components = sub2_components.filter(maintenance_hours__gte=min_hours)
        if max_hours is not None:
            sub2_components = sub2_components.filter(maintenance_hours__lte=max_hours)

        paginator = Paginator(sub2_components, 50)  # Show 50 subcomponents per page.
        page = self.request.GET.get('page')
        try:
            sub2_components = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            sub2_components = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            sub2_components = paginator.page(paginator.num_pages)

        table = Sub2ComponentTable(sub2_components)
        RequestConfig(self.request).configure(table)
        model_name = 'AircraftSubComponent'
        context['model_name'] = model_name
        context['table'] = table
        context['component'] = sub_component
        context['total_components'] = total_sub2_components
        return context


class Sub2ComponentUpdateView(LoginRequiredMixin, UpdateView):
    model = AircraftSub2Component
    template_name = 'maintenance/sub2_component/sub2_component_edit.html'
    context_object_name = 'sub_component'
    form_class = AircraftSub2ComponentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True  # Indicate that this is an update operation
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            sub_2_component = form.save()
            parent_sub_component_pk = sub_2_component.parent_sub_component.pk
            messages.success(self.request, 'Sub of the second Level Component Updated successfully.')
            #return redirect('aircraft_sub_components_list', pk=parent_sub_component_pk)
            return redirect('aircraft_sub2_components_list', pk=parent_sub_component_pk)


@login_required
def add_aircraft_sub3_component(request, sub2_component_id):
    sub2_component = get_object_or_404(AircraftSub2Component, pk=sub2_component_id)
    aircraft = sub2_component.parent_sub_component.parent_component.aircraft_attached

    if request.method == 'POST':
        form = AircraftSub3ComponentForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('multiple_entries'):
                serial_numbers = form.cleaned_data[
                    'serial_numbers']  # Assuming this is already a list or cleaned to be a list
                num_created = 0
                with transaction.atomic():
                    for serial_number in serial_numbers:
                        sub3_component = AircraftSub3Component()
                        for field in form.cleaned_data:
                            if field not in ['multiple_entries', 'serial_numbers']:
                                setattr(sub3_component, field, form.cleaned_data[field])
                        sub3_component.parent_sub2_component = sub2_component
                        sub3_component.added_by = request.user
                        sub3_component.serial_number = serial_number.strip()  # Clean serial number
                        sub3_component.save()
                        num_created += 1
                messages.success(request, f'{num_created} Third Level Components Added Successfully')
            else:
                sub3_component = form.save(commit=False)
                sub3_component.parent_sub2_component = sub2_component
                sub3_component.added_by = request.user
                sub3_component.save()
                messages.success(request, 'Third Level Component Added Successfully')
            return redirect('aircraft_sub3_components_list', pk=sub2_component.id)
    else:
        form = AircraftSub3ComponentForm()

    return render(request, 'maintenance/sub3_component/sub3_component_add.html',
                  {'form': form, 'sub_component': sub2_component, 'aircraft': aircraft})


class Sub3ComponentListView(LoginRequiredMixin, TemplateView):
    template_name = 'maintenance/sub3_component/sub3_component_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_term = self.request.GET.get('search', '')
        min_hours = int(self.request.GET.get('min_hours', '0')) if self.request.GET.get('min_hours') else None
        max_hours = int(self.request.GET.get('max_hours', '0')) if self.request.GET.get('max_hours') else None
        sub2_component_id = self.kwargs['pk']
        sub2_component = get_object_or_404(AircraftSub2Component, pk=sub2_component_id)

        # Only get subcomponents of the given main component
        sub3_components = AircraftSub3Component.objects.filter(parent_sub2_component=sub2_component)
        total_sub3_components = sub3_components.count()

        search_fields = [
            'component_name',
            'parent_sub2_component__component_name',
            'parent_sub2_component__parent_sub_component__parent_component__aircraft_attached__abbreviation'
        ]

        query = Q()
        for field in search_fields:
            query |= Q(**{f'{field}__icontains': search_term})

        sub3_components = sub3_components.filter(
            query
        )

        if min_hours is not None:
            sub3_components = sub3_components.filter(maintenance_hours__gte=min_hours)
        if max_hours is not None:
            sub3_components = sub3_components.filter(maintenance_hours__lte=max_hours)

        paginator = Paginator(sub3_components, 50)  # Show 50 subcomponents per page.
        page = self.request.GET.get('page')
        try:
            sub3_components = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            sub3_components = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            sub3_components = paginator.page(paginator.num_pages)

        table = Sub3ComponentTable(sub3_components)
        RequestConfig(self.request).configure(table)
        model_name = 'AircraftSub2Component'
        context['model_name'] = model_name
        context['table'] = table
        context['component'] = sub2_component
        context['total_components'] = total_sub3_components
        return context


class AircraftSub3ComponentDetailView(DetailView):
    model = AircraftSub3Component
    template_name = 'maintenance/sub3_component/sub3_component_detailed.html'

    def get_context_data(self, **kwargs):
        context = super(AircraftSub3ComponentDetailView, self).get_context_data(**kwargs)
        model_name = 'AircraftSub3Component'
        context['model_name'] = model_name
        context['component'] = context['object']
        return context


class Sub3ComponentUpdateView(LoginRequiredMixin, UpdateView):
    model = AircraftSub3Component
    template_name = 'maintenance/sub3_component/sub3_component_edit.html'
    context_object_name = 'sub_component'
    form_class = AircraftSub2ComponentForm
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_update'] = True  # Indicate that this is an update operation
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            sub_3_component = form.save()
            parent_sub_component_pk = sub_3_component.parent_sub2_component.pk
            messages.success(self.request, 'Sub of the Third Level Component Updated successfully.')
            return redirect('aircraft_sub3_components_list', pk=parent_sub_component_pk)
