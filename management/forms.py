from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Customer, Booking, Project, Unit, Service, BookingService

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "mobile", "nationality", "id_number", "whatsapp", "email"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "mobile": forms.TextInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500",
                "type": "tel"
            }),
            "nationality": forms.TextInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "id_number": forms.TextInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "whatsapp": forms.TextInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500",
                "type": "tel"
            }),
            "email": forms.EmailInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
        }

class BookingForm(forms.ModelForm):
    customer_search = forms.CharField(
        label=_("Search Customer (Name/Mobile)"),
        required=False,
        widget=forms.TextInput(attrs={
            "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500",
            "hx-get": "/customers/search/",
            "hx-trigger": "keyup changed delay:500ms",
            "hx-target": "#customer-search-results",
            "hx-include": "[name='customer_search']",
            "hx-vals": '{"context": "booking"}',
            "placeholder": _("Type customer name or mobile number..."),
            "autocomplete": "off"
        })
    )
    customer_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Booking
        fields = [
            "project", "unit", "customer", "start_date", "end_date",
            "price_per_day", "discount_amount", "discount_percentage",
            "amount_paid", "payment_method",
        ]
        widgets = {
            "project": forms.Select(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500",
                "hx-get": "/htmx/load-units/",
                "hx-target": "#id_unit",
                "hx-trigger": "change"
            }),
            "unit": forms.Select(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "customer": forms.Select(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 customer-select-field"
            }),
            "start_date": forms.DateInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500",
                "type": "date"
            }),
            "end_date": forms.DateInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500",
                "type": "date"
            }),
            "price_per_day": forms.NumberInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "discount_amount": forms.NumberInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "discount_percentage": forms.NumberInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "amount_paid": forms.NumberInput(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "payment_method": forms.Select(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].required = False # Customer is set via customer_id or validated in clean()
        if self.instance and self.instance.pk and self.instance.project_id:
            self.fields["unit"].queryset = Unit.objects.filter(project=self.instance.project)
        elif 'project' in self.data: # if form is bound and project is selected
            try:
                project_id = int(self.data.get('project'))
                self.fields['unit'].queryset = Unit.objects.filter(project_id=project_id).order_by('unit_code')
            except (ValueError, TypeError):
                self.fields['unit'].queryset = Unit.objects.none() # Invalid project ID
        else:
            self.fields["unit"].queryset = Unit.objects.none()


    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        unit = cleaned_data.get("unit")
        customer_id_val = cleaned_data.get("customer_id")

        # --- Modified Customer Validation ---
        if customer_id_val:
            try:
                customer_instance = Customer.objects.get(pk=customer_id_val)
                cleaned_data["customer"] = customer_instance # Set customer in cleaned_data
            except Customer.DoesNotExist:
                self.add_error("customer_search", _("Selected customer not found. Please search again or add a new one."))
                # Raise a general validation error to ensure form invalidation
                raise forms.ValidationError(
                    _("Invalid customer selection: The specified customer does not exist."),
                    code='invalid_customer'
                )

        # After attempting to load customer via customer_id,
        # check if 'customer' is actually populated in cleaned_data.
        if not cleaned_data.get("customer"):
            # If 'customer_search' doesn't already have an error (e.g. from DoesNotExist)
            if 'customer_search' not in self.errors:
                 self.add_error("customer_search", _("A customer must be selected or added for the booking."))
            # Raise a general validation error to ensure form invalidation if no customer resolved
            raise forms.ValidationError(
                _("Customer is required for booking. Please select or add a customer."),
                code='customer_required'
            )
        # --- End of Modified Customer Validation ---

        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                self.add_error("end_date", _("لا يمكن أن يكون تاريخ الانتهاء قبل تاريخ البدء."))

            # Validate unit availability if unit, start_date, and end_date are present
            if unit:
                overlapping_bookings_query = Booking.objects.filter(
                    unit=unit,
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                    status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED]
                )
                if self.instance and self.instance.pk: # If updating, exclude current booking
                    overlapping_bookings_query = overlapping_bookings_query.exclude(pk=self.instance.pk)

                if overlapping_bookings_query.exists():
                    self.add_error("unit", _("هذه الوحدة محجوزة بالفعل في التواريخ المحددة. يرجى اختيار تواريخ أو وحدة مختلفة."))
        
        return cleaned_data

BookingServiceFormSet = forms.inlineformset_factory(
    Booking,
    BookingService,
    fields=("service", "quantity"),
    extra=1,
    can_delete=True,
    widgets={
        "service": forms.Select(attrs={
            "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 service-select"
        }),
        "quantity": forms.NumberInput(attrs={
            "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 quantity-input",
            "min": "1",
            "value": "1"
        }),
    }
)
