from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from management.models import Project, Unit, Customer, Booking, Service
from datetime import date, timedelta
from management.forms import BookingForm

class BookingLogicTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword123')
        self.client = Client()
        self.client.login(username='testuser', password='testpassword123')

        self.project = Project.objects.create(project_code="P001", name="Test Project", total_units=10)
        self.unit1 = Unit.objects.create(project=self.project, unit_code="U001", price_per_day=100.00, status=Unit.UnitStatus.AVAILABLE)
        self.unit2 = Unit.objects.create(project=self.project, unit_code="U002", price_per_day=120.00, status=Unit.UnitStatus.AVAILABLE)
        self.customer1 = Customer.objects.create(name="Test Customer 1", mobile="1234567890")
        self.customer2 = Customer.objects.create(name="Test Customer 2", mobile="0987654321")
        self.service1 = Service.objects.create(service_code="S001", name="Cleaning Service", price=50.00)

        self.booking_add_url = reverse("management:booking_add")
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 1, 5)

    def _create_booking(self, unit, customer, start_date, end_date, status=Booking.BookingStatus.BOOKED, price_per_day=None, amount_paid=0.00):
        if price_per_day is None:
            price_per_day = unit.price_per_day
        return Booking.objects.create(
            project=unit.project,
            unit=unit,
            customer=customer,
            start_date=start_date,
            end_date=end_date,
            price_per_day=price_per_day,
            amount_paid=amount_paid,
            status=status
        )

    def test_create_booking_with_customer_and_unit_status_update(self):
        post_data = {
            "project": self.project.pk, "unit": self.unit1.pk, "customer_id": self.customer1.pk,
            "start_date": self.start_date.strftime("%Y-%m-%d"), "end_date": self.end_date.strftime("%Y-%m-%d"),
            "price_per_day": self.unit1.price_per_day, "discount_amount": "0.00", "discount_percentage": "0.00",
            "amount_paid": "300.00", "payment_method": Booking.PaymentMethod.CASH,
            "services-TOTAL_FORMS": "0", "services-INITIAL_FORMS": "0", "services-MIN_NUM_FORMS": "0", "services-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(self.booking_add_url, data=post_data)
        self.assertEqual(Booking.objects.count(), 1)
        created_booking = Booking.objects.first()
        self.assertRedirects(response, reverse("management:booking_detail", kwargs={"pk": created_booking.pk}))
        self.assertEqual(created_booking.customer, self.customer1)
        self.unit1.refresh_from_db()
        self.assertEqual(self.unit1.status, Unit.UnitStatus.OCCUPIED)

    def test_prevent_double_booking_booked_status_via_form(self):
        self._create_booking(self.unit1, self.customer1, self.start_date, self.end_date, status=Booking.BookingStatus.BOOKED)
        form_data = {
            "project": self.project.pk, "unit": self.unit1.pk, "customer": self.customer2.pk, "customer_id": self.customer2.pk,
            "start_date": self.start_date + timedelta(days=1), "end_date": self.end_date + timedelta(days=1),
            "price_per_day": self.unit1.price_per_day,
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('unit', form.errors)
        self.assertIn("هذه الوحدة محجوزة بالفعل في التواريخ المحددة", form.errors['unit'][0])

    def test_prevent_double_booking_completed_status_via_form(self):
        self._create_booking(self.unit1, self.customer1, self.start_date, self.end_date, status=Booking.BookingStatus.COMPLETED)
        form_data = {
            "project": self.project.pk, "unit": self.unit1.pk, "customer": self.customer2.pk, "customer_id": self.customer2.pk,
            "start_date": self.start_date, "end_date": self.end_date, # Exact overlap
            "price_per_day": self.unit1.price_per_day,
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('unit', form.errors)
        self.assertIn("هذه الوحدة محجوزة بالفعل في التواريخ المحددة", form.errors['unit'][0])

    def test_allow_booking_non_overlapping_dates_via_view(self):
        self._create_booking(self.unit1, self.customer1, self.start_date, self.end_date)
        non_overlapping_start = self.end_date + timedelta(days=1)
        non_overlapping_end = non_overlapping_start + timedelta(days=4)
        post_data = {
            "project": self.project.pk, "unit": self.unit1.pk, "customer_id": self.customer2.pk,
            "start_date": non_overlapping_start.strftime("%Y-%m-%d"), "end_date": non_overlapping_end.strftime("%Y-%m-%d"),
            "price_per_day": self.unit1.price_per_day, "amount_paid": "100.00", "payment_method": Booking.PaymentMethod.CASH,
            "discount_amount": "0.00", "discount_percentage": "0.00", # Added missing fields
            "services-TOTAL_FORMS": "0", "services-INITIAL_FORMS": "0", "services-MIN_NUM_FORMS": "0", "services-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(self.booking_add_url, data=post_data)
        self.assertEqual(Booking.objects.count(), 2)
        new_booking = Booking.objects.filter(customer=self.customer2, start_date=non_overlapping_start).first()
        self.assertIsNotNone(new_booking)
        self.assertRedirects(response, reverse("management:booking_detail", kwargs={"pk": new_booking.pk}))

    def test_allow_booking_cancelled_overlap_via_view(self):
        self._create_booking(self.unit1, self.customer1, self.start_date, self.end_date, status=Booking.BookingStatus.CANCELLED)
        post_data = {
            "project": self.project.pk, "unit": self.unit1.pk, "customer_id": self.customer2.pk,
            "start_date": self.start_date.strftime("%Y-%m-%d"), "end_date": self.end_date.strftime("%Y-%m-%d"),
            "price_per_day": self.unit1.price_per_day, "amount_paid": "100.00", "payment_method": Booking.PaymentMethod.CASH,
            "discount_amount": "0.00", "discount_percentage": "0.00", # Added missing fields
            "services-TOTAL_FORMS": "0", "services-INITIAL_FORMS": "0", "services-MIN_NUM_FORMS": "0", "services-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(self.booking_add_url, data=post_data)
        self.assertEqual(Booking.objects.count(), 2)
        new_booking = Booking.objects.filter(customer=self.customer2, status=Booking.BookingStatus.BOOKED).first()
        self.assertIsNotNone(new_booking)
        self.assertRedirects(response, reverse("management:booking_detail", kwargs={"pk": new_booking.pk}))

    def test_update_booking_same_dates_allowed_via_form(self):
        booking_instance = self._create_booking(self.unit1, self.customer1, self.start_date, self.end_date)
        original_amount_paid = booking_instance.amount_paid # Store original
        new_amount_to_add = 50
        expected_amount_paid = original_amount_paid + new_amount_to_add

        form_data = {
            "project": self.project.pk, "unit": self.unit1.pk, "customer": self.customer1.pk, "customer_id": self.customer1.pk,
            "start_date": self.start_date, "end_date": self.end_date,
            "price_per_day": self.unit1.price_per_day, "amount_paid": expected_amount_paid, # Use the calculated expected amount
            "payment_method": Booking.PaymentMethod.CARD,
            "discount_amount": "0.00", "discount_percentage": "0.00",
            "services-TOTAL_FORMS": "0", "services-INITIAL_FORMS": "0", "services-MIN_NUM_FORMS": "0", "services-MAX_NUM_FORMS": "1000",
        }
        form = BookingForm(data=form_data, instance=booking_instance)
        if not form.is_valid(): print(f"DEBUG test_update_booking_same_dates_allowed_via_form: {form.errors.as_json(escape_html=True)}")
        self.assertTrue(form.is_valid())
        updated_booking = form.save()
        self.assertEqual(updated_booking.amount_paid, expected_amount_paid) # Check against the pre-calculated expected value

    def test_update_booking_to_overlap_another_prevented_via_form(self):
        booking_to_update = self._create_booking(self.unit1, self.customer1, self.start_date, self.end_date)
        conflicting_start = self.end_date + timedelta(days=1)
        conflicting_end = conflicting_start + timedelta(days=4)
        self._create_booking(self.unit1, self.customer2, conflicting_start, conflicting_end) # The other booking

        form_data = { # Try to extend booking_to_update to overlap with the other booking
            "project": self.project.pk, "unit": self.unit1.pk, "customer": self.customer1.pk, "customer_id": self.customer1.pk,
            "start_date": self.start_date, "end_date": conflicting_start + timedelta(days=1), # New end date overlaps
            "price_per_day": self.unit1.price_per_day,
            "services-TOTAL_FORMS": "0", "services-INITIAL_FORMS": "0", "services-MIN_NUM_FORMS": "0", "services-MAX_NUM_FORMS": "1000",
        }
        form = BookingForm(data=form_data, instance=booking_to_update)
        self.assertFalse(form.is_valid())
        self.assertIn('unit', form.errors)
        self.assertIn("هذه الوحدة محجوزة بالفعل في التواريخ المحددة", form.errors['unit'][0])
