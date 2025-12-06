from django.urls import path
from .airport_managment import AirportCreateView, AirportDetailView, AirportListView, AirportUpdateView

from . import views, level_two_three_views
from .level_two_three_views import Sub2ComponentListView, Sub3ComponentListView, AircraftSub3ComponentDetailView, \
    Sub3ComponentUpdateView
from .views import AircraftListView, AircraftDetailView, AircraftUpdateView, SubComponentListView, \
    MainComponentListView, MainComponentUpdateView, SubComponentUpdateView, AircraftMaintenanceTechLogListView, \
    FlightTechLogListView, \
    AircraftMaintenanceTechLogUpdateView, AircraftMaintenanceTechLogDetailView

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
]
