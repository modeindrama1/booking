from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Q, Sum, Count, Avg, F
from .models import Customer, Project, Unit, Booking, Service, BookingService
from .forms import CustomerForm, BookingForm, BookingServiceFormSet
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .pdf_utils import generate_booking_receipt_pdf_response, send_receipt_email
from datetime import datetime, timedelta

# Placeholder Dashboard
@login_required
def dashboard(request):
    project_count = Project.objects.count()
    unit_count = Unit.objects.count()
    customer_count = Customer.objects.count()
    active_booking_count = Booking.objects.filter(status=Booking.BookingStatus.BOOKED).count()
    context = {
        "project_count": project_count,
        "unit_count": unit_count,
        "customer_count": customer_count,
        "active_booking_count": active_booking_count,
    }
    return render(request, "management/dashboard.html", context)

# Customer Views
@login_required
def customer_list(request):
    return render(request, "management/customer_list.html")

@login_required
def customer_search(request):
    query = request.GET.get("q", "")
    # Also check for customer_search parameter which is used in the booking form
    if not query:
        query = request.GET.get("customer_search", "")
    customers = []
    target_template = "management/partials/customer_search_results.html"

    if query:
        customers = Customer.objects.filter(
            Q(name__icontains=query) | Q(mobile__icontains=query)
        )[:10]

    search_context = request.GET.get("context", "list")
    if search_context == "booking":
        target_template = "management/partials/customer_search_results_booking.html"

    if request.headers.get("HX-Request") == "true":
        html = render_to_string(target_template, {"customers": customers})
        return HttpResponse(html)
    else:
        return render(request, "management/customer_list.html", {"customers": customers, "query": query})

@login_required
def customer_select_for_booking(request):
    customer_id = request.GET.get("customer_id")
    try:
        customer = Customer.objects.get(pk=customer_id)
        html = render_to_string("management/partials/customer_selection_booking.html", {"customer": customer})
        return HttpResponse(html)
    except Customer.DoesNotExist:
        return HttpResponse("<p class=\"text-red-500\">Customer not found.</p>", status=404)

@login_required
def customer_add(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            if request.GET.get("next") == "booking":
                html = render_to_string("management/partials/customer_selection_booking.html", {"customer": customer})
                response = HttpResponse(html)
                response["HX-Trigger"] = "customerAdded"
                return response
            else:
                messages.success(request, "Customer added successfully.")
                return redirect("management:customer_list")
    else:
        form = CustomerForm()
    return render(request, "management/customer_form.html", {"form": form, "is_modal": request.headers.get("HX-Request")})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    bookings = Booking.objects.filter(customer=customer).order_by("-booking_datetime")
    context = {
        "customer": customer,
        "bookings": bookings
    }
    return render(request, "management/customer_detail.html", context)

# Booking Views
@login_required
def booking_list(request):
    bookings = Booking.objects.select_related("project", "unit", "customer").order_by("-booking_datetime")
    return render(request, "management/booking_list.html", {"bookings": bookings})

@login_required
@transaction.atomic
def booking_add(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        formset = BookingServiceFormSet(request.POST, prefix="services")

        if form.is_valid() and formset.is_valid():
            booking = form.save(commit=False)
            if not booking.customer:
                 messages.error(request, "Customer was not correctly selected.")
                 context = {"form": form, "formset": formset}
                 return render(request, "management/booking_form.html", context)
            else:
                booking.save()
                formset.instance = booking
                formset.save()
                booking.unit.status = Unit.UnitStatus.OCCUPIED
                booking.unit.save()
                messages.success(request, f"Booking {booking.booking_code} created successfully.")
                email_sent = send_receipt_email(booking)
                if email_sent:
                    messages.info(request, "Receipt email sent successfully.")
                else:
                    messages.warning(request, "Could not send receipt email. Please check settings or customer email.")
                return redirect("management:booking_detail", pk=booking.pk)
        else:
            messages.error(request, "Please correct the errors below.")
            print("Booking Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)
            print("Non-Form Errors:", formset.non_form_errors())
    else:
        form = BookingForm()
        formset = BookingServiceFormSet(prefix="services")
    context = {"form": form, "formset": formset}
    return render(request, "management/booking_form.html", context)

@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("project", "unit", "customer"), pk=pk)
    booking_services = BookingService.objects.filter(booking=booking).select_related("service")
    context = {"booking": booking, "booking_services": booking_services}
    return render(request, "management/booking_detail.html", context)

@login_required
@transaction.atomic
def booking_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        formset = BookingServiceFormSet(request.POST, instance=booking, prefix="services")
        if form.is_valid() and formset.is_valid():
            updated_booking = form.save()
            formset.save()
            messages.success(request, f"Booking {updated_booking.booking_code} updated successfully.")
            return redirect("management:booking_detail", pk=updated_booking.pk)
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = BookingForm(instance=booking)
        formset = BookingServiceFormSet(instance=booking, prefix="services")
    context = {"form": form, "formset": formset, "booking": booking}
    return render(request, "management/booking_form.html", context)

@login_required
@transaction.atomic
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        if booking.status == Booking.BookingStatus.BOOKED:
            booking.status = Booking.BookingStatus.CANCELLED
            booking.save()
            booking.unit.status = Unit.UnitStatus.AVAILABLE
            booking.unit.save()
            messages.success(request, f"Booking {booking.booking_code} cancelled successfully.")
            return redirect("management:booking_list")
        else:
            messages.error(request, f"Booking cannot be cancelled as its status is {booking.get_status_display()}.")
            return redirect("management:booking_detail", pk=booking.pk)
    else:
        return redirect("management:booking_detail", pk=booking.pk)

# PDF Receipt View
@login_required
def booking_receipt_pdf(request, pk):
    booking = get_object_or_404(Booking.objects.select_related("project", "unit", "customer"), pk=pk)
    return generate_booking_receipt_pdf_response(booking)

# HTMX Helper Views
@login_required
def load_units(request):
    project_id = request.GET.get("project")
    try:
        units = Unit.objects.filter(project_id=project_id).order_by("unit_code")
    except ValueError:
        units = Unit.objects.none()
    return render(request, "management/partials/unit_options.html", {"units": units})

@login_required
def check_unit_availability(request):
    unit_id = request.GET.get("unit")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    if not all([unit_id, start_date_str, end_date_str]):
        return HttpResponse("<p class=\"text-orange-500 text-sm\">Please select unit and dates.</p>")
    try:
        unit = Unit.objects.get(pk=unit_id)
        start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        booking_id = request.GET.get("booking_id")
        conflicting_bookings = Booking.objects.filter(
            unit=unit, start_date__lte=end_date, end_date__gte=start_date,
            status=Booking.BookingStatus.BOOKED
        )
        if booking_id:
            conflicting_bookings = conflicting_bookings.exclude(pk=booking_id)
        if conflicting_bookings.exists():
            return HttpResponse("<p class=\"text-red-500 text-sm font-semibold\">Unit not available for these dates.</p>")
        else:
            if unit.status == Unit.UnitStatus.AVAILABLE or (booking_id and Booking.objects.get(pk=booking_id).unit == unit):
                 return HttpResponse("<p class=\"text-green-500 text-sm font-semibold\">Unit is available!</p>")
            else:
                 return HttpResponse("<p class=\"text-red-500 text-sm font-semibold\">Unit is currently marked as Occupied.</p>")
    except (Unit.DoesNotExist, ValueError, Booking.DoesNotExist):
        return HttpResponse("<p class=\"text-red-500 text-sm\">Invalid input or booking not found.</p>")

# Simple Project/Unit List Views
@login_required
def project_list(request):
    projects = Project.objects.all()
    return render(request, "management/project_list.html", {"projects": projects})

@login_required
def unit_list(request):
    units = Unit.objects.select_related("project").all()
    return render(request, "management/unit_list.html", {"units": units})

# Reporting Views
@login_required
def report_dashboard(request):
    # Simple dashboard linking to different reports
    return render(request, "management/report_dashboard.html")

@login_required
def financial_report(request):
    bookings = Booking.objects.filter(status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED])
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    today = timezone.now().date()
    start_date = today - timedelta(days=30) # Default to last 30 days
    end_date = today

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid start date format. Use YYYY-MM-DD.")
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid end date format. Use YYYY-MM-DD.")

    # Filter by booking creation date for financial tracking
    bookings = bookings.filter(booking_datetime__date__range=[start_date, end_date])

    total_revenue = bookings.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    total_final_amount = bookings.aggregate(Sum(F("price_per_day") * (F("end_date") - F("start_date") + timedelta(days=1)) - F("discount_amount") - (F("price_per_day") * (F("end_date") - F("start_date") + timedelta(days=1)) * F("discount_percentage") / 100))) # Approximation, need to add service cost
    # Note: Calculating final_amount accurately in aggregate is complex due to properties and M2M. Summing amount_paid is more direct for cash flow.
    total_discount = bookings.aggregate(
        total_discount_amount=Sum("discount_amount"),
        # Add calculation for percentage discount if needed
    )
    total_bookings = bookings.count()

    context = {
        "bookings": bookings.order_by("-booking_datetime"),
        "total_revenue": total_revenue,
        "total_bookings": total_bookings,
        "total_discount_amount": total_discount["total_discount_amount"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    return render(request, "management/financial_report.html", context)

@login_required
def project_report(request):
    project_id = request.GET.get("project_id")
    projects_summary = Project.objects.annotate(
        num_bookings=Count("booking", filter=Q(booking__status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED])),
        total_paid=Sum("booking__amount_paid", filter=Q(booking__status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED]))
    ).order_by("-total_paid")

    selected_project_bookings = None
    selected_project = None
    if project_id:
        try:
            selected_project = Project.objects.get(pk=project_id)
            selected_project_bookings = Booking.objects.filter(project=selected_project).select_related("unit", "customer").order_by("-booking_datetime")
        except (Project.DoesNotExist, ValueError):
            messages.error(request, "Invalid Project selected.")

    context = {
        "projects_summary": projects_summary,
        "projects_list": Project.objects.all(), # For dropdown filter
        "selected_project_id": project_id,
        "selected_project": selected_project,
        "selected_project_bookings": selected_project_bookings,
    }
    return render(request, "management/project_report.html", context)

@login_required
def unit_report(request):
    project_id = request.GET.get("project_id")
    unit_id = request.GET.get("unit_id")

    units_query = Unit.objects.select_related("project")
    if project_id:
        units_query = units_query.filter(project_id=project_id)

    units_summary = units_query.annotate(
        num_bookings=Count("booking", filter=Q(booking__status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED])),
        total_paid=Sum("booking__amount_paid", filter=Q(booking__status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED]))
    ).order_by("-total_paid")

    selected_unit_bookings = None
    selected_unit = None
    if unit_id:
        try:
            selected_unit = Unit.objects.select_related("project").get(pk=unit_id)
            selected_unit_bookings = Booking.objects.filter(unit=selected_unit).select_related("customer").order_by("-booking_datetime")
        except (Unit.DoesNotExist, ValueError):
            messages.error(request, "Invalid Unit selected.")

    context = {
        "units_summary": units_summary,
        "projects_list": Project.objects.all(), # For dropdown filter
        "selected_project_id": project_id,
        "selected_unit_id": unit_id,
        "selected_unit": selected_unit,
        "selected_unit_bookings": selected_unit_bookings,
    }
    return render(request, "management/unit_report.html", context)

@login_required
def discount_report(request):
    # Bookings with any discount applied
    discounted_bookings = Booking.objects.filter(
        Q(discount_amount__gt=0) | Q(discount_percentage__gt=0),
        status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED]
    ).select_related("project", "unit", "customer").order_by("-booking_datetime")

    total_discount_given = discounted_bookings.aggregate(Sum("discount_amount"))["discount_amount__sum"] or 0
    # Add calculation for percentage discounts if needed

    context = {
        "discounted_bookings": discounted_bookings,
        "total_discount_given": total_discount_given,
    }
    return render(request, "management/discount_report.html", context)

@login_required
def cancellation_refund_report(request):
    cancelled_bookings = Booking.objects.filter(
        status__in=[Booking.BookingStatus.CANCELLED, Booking.BookingStatus.REFUNDED]
    ).select_related("project", "unit", "customer").order_by("-booking_datetime")

    context = {
        "cancelled_bookings": cancelled_bookings,
    }
    return render(request, "management/cancellation_refund_report.html", context)

# Need to create templates: report_dashboard.html, financial_report.html, project_report.html, unit_report.html, discount_report.html, cancellation_refund_report.html
# Also need templates for project_list.html, unit_list.html if not using admin exclusively.
# Also need base template and partials for HTMX interactions.

