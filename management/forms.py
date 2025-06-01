from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Customer, Booking, Project, Unit, Service, BookingService

class CustomerForm(forms.ModelForm):
    """
    Form for creating and updating Customer instances.
    """
    class Meta:
        model = Customer
        fields = ["name", "mobile", "nationality", "id_number", "whatsapp", "email"]
        # To translate labels for these fields, ensure `verbose_name` is set
        # and translated in your Customer model (models.py). For example:
        # name = models.CharField(_("Name"), max_length=100)
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
    """
    Form for creating and updating Booking instances.
    Includes HTMX integration for customer search and dynamic unit loading.
    """
    # Field for customer search/selection, used when creating a new booking
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
    # Hidden field to store the ID of the selected customer
    customer_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Booking
        fields = [
            "project", "unit", "customer", "start_date", "end_date",
            "price_per_day", "discount_amount", "discount_percentage",
            "amount_paid", "payment_method",
            # additional_services are handled separately via a formset
        ]
        # To translate labels for these fields, ensure `verbose_name` is set
        # and translated in your Booking model (models.py).
        widgets = {
            "project": forms.Select(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500",
                "hx-get": "/htmx/load-units/",  # URL to load units based on selected project
                "hx-target": "#id_unit",      # Target select field for units
                "hx-trigger": "change"
            }),
            "unit": forms.Select(attrs={
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            }),
            "customer": forms.Select(attrs={ # This field might be hidden or populated by the customer search logic
                "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 customer-select-field"
                # Adding a class to potentially hide/show this field with JS if needed
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
        """
        Initializes the BookingForm.
        - Sets the customer field as not required initially (will be set via search).
        - Dynamically sets the queryset for units based on the project if an instance exists.
        - Starts with an empty queryset for units if no project is selected (populated by HTMX).
        """
        super().__init__(*args, **kwargs)
        # The 'customer' ForeignKey field is made not required initially because
        # it will be populated via the 'customer_id' hidden field after a search.
        self.fields["customer"].required = False

        # If editing an existing booking, populate the unit dropdown based on the current project.
        if self.instance and self.instance.pk and self.instance.project_id: # Check self.instance.pk to ensure it's a saved instance
            self.fields["unit"].queryset = Unit.objects.filter(project=self.instance.project)
        elif 'project' in self.data: # if form is bound and project is selected
            try:
                project_id = int(self.data.get('project'))
                self.fields['unit'].queryset = Unit.objects.filter(project_id=project_id).order_by('unit_code')
            except (ValueError, TypeError):
                self.fields['unit'].queryset = Unit.objects.none() # Invalid project ID
        else:
            # For new bookings, or if no project is selected, start with an empty queryset for units.
            # This will be populated dynamically by HTMX when a project is chosen.
            self.fields["unit"].queryset = Unit.objects.none()


    def clean(self):
        """
        Custom validation for the BookingForm.
        - Ensures a customer is selected (either via hidden ID or direct field).
        - Validates that the end date is not before the start date.
        - Checks for overlapping bookings for the selected unit and dates.
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        unit = cleaned_data.get("unit")
        customer_id = cleaned_data.get("customer_id") # From hidden input
        customer_instance = cleaned_data.get("customer") # From the actual model field

        # Validate customer selection:
        # If customer_id is present (from search), try to fetch the customer.
        if customer_id:
            try:
                cleaned_data["customer"] = Customer.objects.get(pk=customer_id)
            except Customer.DoesNotExist:
                self.add_error("customer_search", _("Selected customer not found. Please search again."))
        # If no customer_id and no customer instance (e.g. if direct select was used but somehow empty)
        elif not customer_instance:
                self.add_error("customer_search", _("Please select or search for a customer."))


        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                self.add_error("end_date", _("لا يمكن أن يكون تاريخ الانتهاء قبل تاريخ البدء.")) # Translated

            # Validate unit availability if unit, start_date, and end_date are present
            if unit:
                # Check for overlapping bookings, excluding the current booking instance if it's being edited.
                overlapping_bookings_query = Booking.objects.filter(
                    unit=unit,
                    start_date__lte=end_date,  # A booking overlaps if its start is before or on our end
                    end_date__gte=start_date,    # And its end is after or on our start
                    status__in=[Booking.BookingStatus.BOOKED, Booking.BookingStatus.COMPLETED] # Consider only active bookings
                )
                if self.instance and self.instance.pk:
                    overlapping_bookings_query = overlapping_bookings_query.exclude(pk=self.instance.pk)

                if overlapping_bookings_query.exists():
                    self.add_error("unit", _("هذه الوحدة محجوزة بالفعل في التواريخ المحددة. يرجى اختيار تواريخ أو وحدة مختلفة.")) # Translated
        
        return cleaned_data

# Formset for adding/editing additional services related to a booking
BookingServiceFormSet = forms.inlineformset_factory(
    Booking,  # Parent model
    BookingService,  # Child model
    fields=("service", "quantity"),
    # To translate labels for these fields, ensure `verbose_name` is set
    # and translated in your BookingService model (models.py).
    extra=1,  # Number of empty forms to display
    can_delete=True,  # Allows deletion of existing related objects
    widgets={
        "service": forms.Select(attrs={
            "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 service-select"
        }),
        "quantity": forms.NumberInput(attrs={
            "class": "mt-1 block w-full px-3 py-2 bg-white border border-slate-300 rounded-md text-sm shadow-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 quantity-input",
            "min": "1", # Quantity should be at least 1
            "value": "1" # Default quantity to 1
        }),
    }
)
