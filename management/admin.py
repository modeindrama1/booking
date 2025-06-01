from django.contrib import admin
from django.utils.translation import gettext_lazy as _ # Moved import to the top
from .models import Project, Unit, Service, Customer, Booking, BookingService

class UnitInline(admin.TabularInline):
    model = Unit
    extra = 1 # Number of empty forms to display
    fields = ("unit_code", "description", "status", "image")
    readonly_fields = ("status",) # Status should be managed via booking

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("project_code", "name", "address", "total_units", "manager_name")
    search_fields = ("project_code", "name", "manager_name")
    inlines = [UnitInline]

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("unit_code", "project", "description", "status")
    list_filter = ("project", "status")
    search_fields = ("unit_code", "project__name", "description")
    list_select_related = (
        "project",
    ) # Optimize query

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("service_code", "name", "price", "description")
    search_fields = ("service_code", "name")

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "nationality", "id_number", "whatsapp", "email")
    search_fields = ("name", "mobile", "id_number", "email")

class BookingServiceInline(admin.TabularInline):
    model = BookingService
    extra = 1
    fields = ("service", "quantity", "price_at_booking")
    readonly_fields = ("price_at_booking",)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "booking_code",
        "customer",
        "project",
        "unit",
        "start_date",
        "end_date",
        "duration_days",
        "final_amount",
        "amount_paid",
        "remaining_amount",
        "status",
        "booking_datetime",
    )
    list_filter = ("status", "project", "payment_method", "start_date", "end_date")
    search_fields = (
        "booking_code",
        "customer__name",
        "customer__mobile",
        "unit__unit_code",
        "project__name",
    )
    readonly_fields = (
        "booking_code",
        "booking_datetime",
        "duration_days",
        "total_base_price",
        "total_discount",
        "total_service_cost",
        "final_amount",
        "remaining_amount",
    )
    fieldsets = (
        (
            _("Booking Info"),
            {
                "fields": (
                    "booking_code",
                    "customer",
                    "project",
                    "unit",
                    "start_date",
                    "end_date",
                    "status",
                    "booking_datetime",
                )
            },
        ),
        (
            _("Pricing & Payment"),
            {
                "fields": (
                    "price_per_day",
                    "discount_amount",
                    "discount_percentage",
                    "amount_paid",
                    "payment_method",
                )
            },
        ),
        (
            _("Calculated Totals"),
            {
                "fields": (
                    "duration_days",
                    "total_base_price",
                    "total_discount",
                    "total_service_cost",
                    "final_amount",
                    "remaining_amount",
                ),
                "classes": ("collapse",), # Collapsed by default
            },
        ),
    )
    inlines = [BookingServiceInline]
    list_select_related = ("customer", "project", "unit") # Optimize queries

    # Add action for marking bookings as cancelled or refunded (requires admin permission)
    actions = ["mark_as_cancelled", "mark_as_refunded"]

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=Booking.BookingStatus.CANCELLED)
        # Add logic here to potentially make the unit available again
        for booking in queryset:
            if booking.unit.status == Unit.UnitStatus.OCCUPIED: # Only free if occupied by this booking
                 # Need more robust logic here, check if *this* booking made it occupied
                 # For now, simple logic: if cancelled, make available
                 booking.unit.status = Unit.UnitStatus.AVAILABLE
                 booking.unit.save()
    mark_as_cancelled.short_description = _("Mark selected bookings as Cancelled")

    def mark_as_refunded(self, request, queryset):
        # Add logic to check if refund is allowed based on status
        allowed_statuses = [Booking.BookingStatus.CANCELLED, Booking.BookingStatus.COMPLETED]
        valid_bookings = queryset.filter(status__in=allowed_statuses)
        valid_bookings.update(status=Booking.BookingStatus.REFUNDED)
        # Optionally add a message for bookings not updated
        # self.message_user(request, f"{queryset.count() - valid_bookings.count()} bookings could not be marked as refunded due to their status.", level=messages.WARNING)

    mark_as_refunded.short_description = _("Mark selected bookings as Refunded")

# Note: BookingService is managed via BookingAdmin inline
# admin.site.register(BookingService) # Not needed if only managed inline

