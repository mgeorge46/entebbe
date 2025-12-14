from django.urls import path
from .airport_managment import AirportCreateView, AirportDetailView, AirportListView, AirportUpdateView

from . import views, level_two_three_views
from .level_two_three_views import Sub2ComponentListView, Sub3ComponentListView, AircraftSub3ComponentDetailView, \
    Sub3ComponentUpdateView

from .views import (
    #Aircraft Views
    AircraftListView,
    AircraftDetailView,
    AircraftUpdateView,
    
    #Component Views
    SubComponentListView,
    MainComponentListView,
    MainComponentUpdateView,
    SubComponentUpdateView,
    
    # TechLog Views
    AircraftMaintenanceTechLogListView,
    FlightTechLogListView,
    AircraftMaintenanceTechLogUpdateView,
    AircraftMaintenanceTechLogDetailView,
    
    # Aircraft Maintenance Scheduling Views
    AircraftMaintenanceListView,
    AircraftMaintenanceCreateView,
    AircraftMaintenanceUpdateView,
    AircraftMaintenanceDetailView,
    
    # Component Maintenance Scheduling Views
    ComponentMaintenanceListView,
    component_maintenance_create,
    ComponentMaintenanceUpdateView,
    ComponentMaintenanceDetailView,
    
    # Helper Views
    get_components_by_aircraft_and_type,
    batch_maintenance_view,
    quick_schedule_component_maintenance,
    auto_schedule_component_maintenance,
    maintenance_dashboard,
    # Two state workflows 
    ComponentMaintenanceCreateView,
    complete_component_maintenance,
    batch_complete_maintenance,
    search_components_ajax,
    component_maintenance_create_enhanced,
    confirm_component_maintenance,
    bulk_confirm_maintenances,
)


urlpatterns = [
    path('aircraft/add/', views.create_aircraft, name='add_aircraft'),
    path('aircraft/list/', AircraftListView.as_view(), name='list_aircraft'),
    path('aircraft/<str:registration_number>/', AircraftDetailView.as_view(), name='aircraft_detail'),
    #path('aircraft/<slug:registration_number>/', AircraftDetailView.as_view(), name='aircraft_detail'),
    path('aircraft/update/<int:pk>/', AircraftUpdateView.as_view(), name='aircraft_edit'),
    # cloning and bulky import component
    path('aircraft/clone/<int:pk>/', views.clone_component_generic, name='clone_component'),
    path('component/clone/<str:model_name>/<int:instance_id>/', views.clone_component_generic,
         name='clone_component_generic'),
    path('aircraft/import/bulky/<slug:registration_number>/', views.bluky_import_aircraft_components, name='bulk_component_import'),

    # Aircraft main Components
    path('aircraft/component/add/<int:aircraft_id>/', views.add_aircraft_main_component,
         name='add_aircraft_main_component'),
    path('aircraft/components/main/list/<int:pk>/', MainComponentListView.as_view(),
         name='aircraft_main_components_list'),
    path('aircraft/components/main/update/<int:pk>', MainComponentUpdateView.as_view(),
         name='aircraft_main_components_update'),
    # Aircraft sub-Components
    path('aircraft/components/main/sub/first/list/<int:pk>/', SubComponentListView.as_view(),
         name='aircraft_sub_components_list'),
    path('aircraft/component/sub/add/<int:main_component_id>/', views.add_aircraft_sub_component,
         name='add_aircraft_sub_component'),
    path('aircraft/components/main/sub/first/update/<int:pk>/', SubComponentUpdateView.as_view(),
         name='aircraft_sub_components_update'),
    # Aircraft sub second level-Components
    path('aircraft/components/main/sub/first/second/list/<int:pk>/', Sub2ComponentListView.as_view(),
         name='aircraft_sub2_components_list'),
    path('aircraft/component/main/sub/first/second/add/<int:sub_component_id>/',
         level_two_three_views.add_aircraft_sub2_component,
         name='add_aircraft_sub2_component'),
    path('aircraft/components/main/sub/first/second/update/<int:pk>/',
         level_two_three_views.Sub2ComponentUpdateView.as_view(), name='aircraft_sub2_components_update'),
    # Aircraft sub third level-Components
    path('aircraft/components/main/sub/first/second/third/list/<int:pk>/', Sub3ComponentListView.as_view(),
         name='aircraft_sub3_components_list'),
    path('aircraft/component/main/sub/first/second/third/add/<int:sub2_component_id>/',
         level_two_three_views.add_aircraft_sub3_component,
         name='add_aircraft_sub3_component'),

    # last level view
    path('aircraft/components/main/sub/first/second/third/last/details/<int:pk>/',
         AircraftSub3ComponentDetailView.as_view(),
         name='aircraft_sub3_components_detail'),
    path('aircraft/components/main/sub/first/second/third/last/edit/<int:pk>/',
         Sub3ComponentUpdateView.as_view(),
         name='sub3_components_edit'),
    # Flight Tech log
    path('aircraft/<str:registration_number>/flight/techlog/', views.FlightTechLogCreateView.as_view(),
         name='create_flighttechlog'),
    path('aircraft/maintenance/techlog/', AircraftMaintenanceTechLogListView.as_view(),
         name='aircraft_maintenance_techlog_list'),
    path('aircraft/flight/techlog/', FlightTechLogListView.as_view(), name='flight_techlog_list'),
    path('aircraft/maintenance/techlog/add/', views.create_aircraft_maintenance_techlog,
         name='add_aircraft_maintenance_techlog'),
    path('aircraft/maintenance/techlog/update/<int:pk>/', AircraftMaintenanceTechLogUpdateView.as_view(),
         name='update_aircraft_maintenance_techlog'),
    path('aircraft/maintenance/techlog/detail/<int:pk>/', AircraftMaintenanceTechLogDetailView.as_view(),
         name='maintenance_techlog_detail'),

    # Airport Management
    path('airport/add/', AirportCreateView.as_view(), name='airport_add'),
    path('airport/list/', AirportListView.as_view(), name='airport_list'),
    path('airport/<int:pk>/edit/', AirportUpdateView.as_view(), name='airport_edit'),
    path('airport/detail/<int:pk>/', AirportDetailView.as_view(), name='airport_detail'),
    # Tree List
    path('xxx/dd', views.component_tree_view, name='tree_view'),

      # ==================== MAINTENANCE DASHBOARD ====================
    path('dashboard/', maintenance_dashboard, name='maintenance_dashboard'),
    
    # ==================== AIRCRAFT MAINTENANCE SCHEDULING ====================
    path('aircraft/schedule/list/', AircraftMaintenanceListView.as_view(), name='aircraft_maintenance_list'),
    
    path('aircraft/schedule/add/', AircraftMaintenanceCreateView.as_view(), name='aircraft_maintenance_add'),
    
    path('aircraft/schedule/update/<int:pk>/',  AircraftMaintenanceUpdateView.as_view(), name='aircraft_maintenance_update'),
    
    path('aircraft/schedule/detail/<int:pk>/', AircraftMaintenanceDetailView.as_view(), name='aircraft_maintenance_detail'),
    
    # ==================== COMPONENT MAINTENANCE SCHEDULING ====================
    path('component/schedule/list/', ComponentMaintenanceListView.as_view(), name='component_maintenance_list'),
    path('component/schedule/create/', ComponentMaintenanceCreateView.as_view(), name='component_maintenance_create'),
    path('component/schedule/update/<int:pk>/', ComponentMaintenanceUpdateView.as_view(), name='component_maintenance_update'),
    path('component/schedule/detail/<int:pk>/', ComponentMaintenanceDetailView.as_view(), name='component_maintenance_detail'),
    # Quick schedule from component detail page
    path('component/<str:model_name>/<int:component_id>/quick-schedule/', quick_schedule_component_maintenance, 
         name='quick_schedule_component'),
    
    # Auto schedule (triggered when component reaches critical hours)
    path('component/<str:model_name>/<int:component_id>/auto-schedule/', auto_schedule_component_maintenance, name='auto_schedule_component'),
    # ==================== BATCH MAINTENANCE ====================
    path('batch/<str:batch_id>/', batch_maintenance_view, name='batch_maintenance_view'),
    # ==================== AJAX ENDPOINTS ====================
    path('ajax/components-by-type/', get_components_by_aircraft_and_type, name='ajax_get_components_by_type'),

     #======================== Two state workflows ========================
     path('component/schedule/create/', component_maintenance_create_enhanced, name='component_maintenance_create'),
     path('component/maintenance/<int:pk>/complete/', complete_component_maintenance, name='complete_component_maintenance'),
     path('batch/<str:batch_id>/complete/', batch_complete_maintenance, name='batch_complete_maintenance'),
     path('ajax/search-components/', search_components_ajax, name='ajax_search_components'),
     # Confirmation actions
     path('component/maintenance/<int:pk>/confirm/', confirm_component_maintenance, name='confirm_component_maintenance'),
     path('component/maintenance/bulk-confirm/', bulk_confirm_maintenances, name='bulk_confirm_maintenances'),
  
]