from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class Project(models.Model):
    project_code = models.CharField(_("Project Code"), max_length=50, unique=True)
    name = models.CharField(_("Project Name"), max_length=200)
    address = models.TextField(_("Address"))
    total_units = models.PositiveIntegerField(_("Total Units"))
    image = models.ImageField(_("Image"), upload_to='project_images/', blank=True, null=True)
    manager_name = models.CharField(_("Manager Name"), max_length=150)

    class Meta:
        verbose_name = _("مشروع")
        verbose_name_plural = _("مشاريع")

    def __str__(self):
        return self.name

class Unit(models.Model):
    class UnitStatus(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        OCCUPIED = 'occupied', _('Occupied')

    project = models.ForeignKey(Project, related_name='units', on_delete=models.CASCADE, verbose_name=_("Project"))
    unit_code = models.CharField(_("Unit Code"), max_length=50, unique=True)
    price_per_day = models.DecimalField(_("Price Per Day (SAR)"), max_digits=10, decimal_places=2)
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(_("Image"), upload_to='unit_images/', blank=True, null=True)
    status = models.CharField(_("Status"), max_length=10, choices=UnitStatus.choices, default=UnitStatus.AVAILABLE)

    class Meta:
        verbose_name = _("وحدة")
        verbose_name_plural = _("وحدات")

    def __str__(self):
        return f"{self.project.name} - {self.unit_code}"

class Service(models.Model):
    service_code = models.CharField(_("Service Code"), max_length=50, unique=True)
    name = models.CharField(_("Service Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("خدمة")
        verbose_name_plural = _("خدمات")

    def __str__(self):
        return self.name

class Customer(models.Model):
    # customer_code = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=200)
    mobile = models.CharField(_("Mobile"), max_length=20, unique=True)
    nationality = models.CharField(_("Nationality"), max_length=100, blank=True)
    id_number = models.CharField(_("ID Number"), max_length=50, blank=True)
    whatsapp = models.CharField(_("WhatsApp"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("مستخدمين")

    def __str__(self):
        return self.name

class Booking(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        CARD = 'card', _('Card (Visa)')
        TRANSFER = 'transfer', _('Bank Transfer')

    class BookingStatus(models.TextChoices):
        BOOKED = 'booked', _('Booked')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded') # For returns/refunds

    booking_code = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name=_("Project"))
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, verbose_name=_("Unit"))
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name=_("Customer"))
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    price_per_day = models.DecimalField(_("Price Per Day (SAR)"), max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(_("Discount Amount (SAR)"), max_digits=10, decimal_places=2, default=0.00)
    discount_percentage = models.DecimalField(_("Discount Percentage (%)"), max_digits=5, decimal_places=2, default=0.00) # e.g., 10.50 for 10.5%
    amount_paid = models.DecimalField(_("Amount Paid (SAR)"), max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(_("Payment Method"), max_length=10, choices=PaymentMethod.choices, blank=True)
    booking_datetime = models.DateTimeField(_("Booking Datetime"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=10, choices=BookingStatus.choices, default=BookingStatus.BOOKED)
    additional_services = models.ManyToManyField(Service, through='BookingService', blank=True, verbose_name=_("Additional Services"))

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1 # Inclusive of start and end date
        return 0

    @property
    def total_base_price(self):
        # Ensure both price_per_day and duration_days are not None
        if not hasattr(self, 'price_per_day') or self.price_per_day is None:
            return 0
        days = self.duration_days
        if days is None:
            return 0
        return self.price_per_day * days

    @property
    def total_discount(self):
        discount_from_amount = self.discount_amount or 0
        if self.total_base_price is None or self.discount_percentage is None:
            discount_from_percentage = 0
        else:
            discount_from_percentage = (self.total_base_price * self.discount_percentage) / 100
        return discount_from_amount + discount_from_percentage

    @property
    def total_service_cost(self):
        try:
            return sum((bs.price_at_booking or 0) * (bs.quantity or 0) for bs in self.bookingservice_set.all())
        except (TypeError, AttributeError):
            return 0

    @property
    def final_amount(self):
        base_price = self.total_base_price or 0
        discount = self.total_discount or 0
        service_cost = self.total_service_cost or 0
        return base_price - discount + service_cost

    @property
    def remaining_amount(self):
        final = self.final_amount or 0
        paid = self.amount_paid or 0
        return final - paid

    class Meta:
        verbose_name = _("حجز")
        verbose_name_plural = _("حجوزات")

    def __str__(self):
        return f"Booking {self.booking_code} for {self.customer.name} in {self.unit.unit_code}"

class BookingService(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    price_at_booking = models.DecimalField(_("Price at Booking (SAR)"), max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('booking', 'service')

    def save(self, *args, **kwargs):
        if not self.pk: # Only set price_at_booking on creation
            self.price_at_booking = self.service.price
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("خدمة حجز")
        verbose_name_plural = _("خدمات حجز")
        
    def __str__(self):
        return f"{self.quantity} x {self.service.name} for Booking {self.booking.booking_code}"


