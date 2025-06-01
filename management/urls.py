from django.urls import path
from . import views

app_name = 'management'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/search/', views.customer_search, name='customer_search'), # For HTMX search
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/select-for-booking/', views.customer_select_for_booking, name='customer_select_for_booking'), # HTMX endpoint

    # Booking URLs
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/add/', views.booking_add, name='booking_add'),
    path('bookings/<uuid:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<uuid:pk>/update/', views.booking_update, name='booking_update'),
    path('bookings/<uuid:pk>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('bookings/<uuid:pk>/receipt/', views.booking_receipt_pdf, name='booking_receipt_pdf'), # PDF Receipt URL

    # HTMX Helper URLs for Booking Form
    path('htmx/load-units/', views.load_units, name='load_units'),
    path('htmx/check-unit-availability/', views.check_unit_availability, name='check_unit_availability'),

    # Project/Unit/Service Views (Simple Lists)
    path('projects/', views.project_list, name='project_list'),
    path('units/', views.unit_list, name='unit_list'),

    # Reporting URLs
    path('reports/', views.report_dashboard, name='report_dashboard'),
    path('reports/financial/', views.financial_report, name='financial_report'),
    path('reports/projects/', views.project_report, name='project_report'),
    path('reports/units/', views.unit_report, name='unit_report'),
    path('reports/discounts/', views.discount_report, name='discount_report'),
    path('reports/cancellations/', views.cancellation_refund_report, name='cancellation_refund_report'),

]

