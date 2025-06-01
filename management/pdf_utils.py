from fpdf import FPDF
from django.http import HttpResponse
from .models import Booking, BookingService
from django.utils import timezone
import os
from django.core.mail import EmailMessage
from django.conf import settings

# Define path to font supporting Arabic
ARABIC_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

class PDFReceipt(FPDF):
    def header(self):
        if os.path.exists(ARABIC_FONT_PATH):
            self.add_font("NotoSansCJK", fname=ARABIC_FONT_PATH)
            self.set_font("NotoSansCJK", size=12)
        else:
            self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "Watad Company", border=0, ln=1, align="C")
        self.set_font(self.font_family, size=10)
        self.cell(0, 5, "Real Estate Project Management", border=0, ln=1, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        if os.path.exists(ARABIC_FONT_PATH):
            self.set_font("NotoSansCJK", size=8)
        else:
            self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")
        self.set_x(10)
        self.cell(0, 10, f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, "L")

    def chapter_title(self, title):
        if os.path.exists(ARABIC_FONT_PATH):
            self.set_font("NotoSansCJK", size=12)
        else:
            self.set_font("helvetica", "B", 12)
        self.cell(0, 6, title, 0, 1, "L", False)
        self.ln(4)

    def chapter_body(self, data):
        if os.path.exists(ARABIC_FONT_PATH):
            self.set_font("NotoSansCJK", size=10)
        else:
            self.set_font("times", size=10)
        for key, value in data.items():
            self.set_font(self.font_family, "B")
            self.cell(40, 6, f"{key}:", 0, 0, "L")
            self.set_font(self.font_family, "")
            self.multi_cell(0, 6, str(value), 0, 1, "L")
        self.ln()

    def add_table(self, header, data):
        if os.path.exists(ARABIC_FONT_PATH):
            self.set_font("NotoSansCJK", size=10)
        else:
            self.set_font("helvetica", "B", 10)
        col_width = self.w / (len(header) + 1)
        line_height = self.font_size * 1.5
        for i, col_title in enumerate(header):
            width = col_width * 1.5 if i == 0 else col_width * 0.8 if i == 1 else col_width
            self.cell(width, line_height, col_title, border=1, ln=0, align="C")
        self.ln(line_height)
        if os.path.exists(ARABIC_FONT_PATH):
            self.set_font("NotoSansCJK", size=9)
        else:
            self.set_font("times", size=9)
        for row in data:
            for i, item in enumerate(row):
                width = col_width * 1.5 if i == 0 else col_width * 0.8 if i == 1 else col_width
                self.cell(width, line_height, str(item), border=1, ln=0, align="L")
            self.ln(line_height)
        self.ln(5)

def generate_pdf_bytes(booking: Booking) -> bytes:
    pdf = PDFReceipt()
    pdf.add_page()
    pdf.alias_nb_pages()

    # Booking Info
    pdf.chapter_title("Booking Details")
    booking_data = {
        "Booking Code": str(booking.booking_code),
        "Project": booking.project.name,
        "Unit": booking.unit.unit_code,
        "Start Date": booking.start_date.strftime("%Y-%m-%d"),
        "End Date": booking.end_date.strftime("%Y-%m-%d"),
        "Duration": f"{booking.duration_days} days",
        "Status": booking.get_status_display(),
        "Booking Time": booking.booking_datetime.strftime("%Y-%m-%d %H:%M"),
    }
    pdf.chapter_body(booking_data)

    # Customer Info
    pdf.chapter_title("Customer Information")
    customer_data = {
        "Name": booking.customer.name,
        "Mobile": booking.customer.mobile,
        "Nationality": booking.customer.nationality or "N/A",
        "ID Number": booking.customer.id_number or "N/A",
        "WhatsApp": booking.customer.whatsapp or "N/A",
        "Email": booking.customer.email or "N/A",
    }
    pdf.chapter_body(customer_data)

    # Pricing
    pdf.chapter_title("Financial Summary")
    pricing_data = {
        "Price Per Day (SAR)": f"{booking.price_per_day:.2f}",
        "Total Base Price (SAR)": f"{booking.total_base_price:.2f}",
        "Discount Amount (SAR)": f"{booking.discount_amount:.2f}",
        "Discount Percentage (%)": f"{booking.discount_percentage:.2f}",
        "Total Discount (SAR)": f"{booking.total_discount:.2f}",
    }
    pdf.chapter_body(pricing_data)

    # Services
    booking_services = BookingService.objects.filter(booking=booking).select_related("service")
    if booking_services.exists():
        pdf.chapter_title("Additional Services")
        service_header = ["Service", "Quantity", "Price/Unit (SAR)", "Total (SAR)"]
        service_rows = []
        for bs in booking_services:
            service_total = bs.quantity * bs.price_at_booking
            service_rows.append([
                bs.service.name,
                bs.quantity,
                f"{bs.price_at_booking:.2f}",
                f"{service_total:.2f}"
            ])
        pdf.add_table(service_header, service_rows)
        pdf.chapter_body({"Total Service Cost (SAR)": f"{booking.total_service_cost:.2f}"})

    # Payment Summary
    pdf.chapter_title("Payment Details")
    payment_data = {
        "Final Amount Due (SAR)": f"{booking.final_amount:.2f}",
        "Amount Paid (SAR)": f"{booking.amount_paid:.2f}",
        "Remaining Amount (SAR)": f"{booking.remaining_amount:.2f}",
        "Payment Method": booking.get_payment_method_display() or "N/A",
    }
    pdf.chapter_body(payment_data)

    # Return PDF content as bytes
    return pdf.output(dest="S").encode("latin-1")

def generate_booking_receipt_pdf_response(booking: Booking):
    pdf_content = generate_pdf_bytes(booking)
    response = HttpResponse(pdf_content, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=receipt_{booking.booking_code}.pdf"
    return response

def send_receipt_email(booking: Booking):
    subject = f"Booking Receipt - Watad Company - Booking {booking.booking_code}"
    body = f"Dear {booking.customer.name},\n\nPlease find attached the receipt for your booking ({booking.booking_code}) with Watad Company.\n\nProject: {booking.project.name}\nUnit: {booking.unit.unit_code}\nDates: {booking.start_date} to {booking.end_date}\n\nThank you for choosing Watad Company."
    from_email = settings.DEFAULT_FROM_EMAIL
    admin_email = settings.ADMIN_EMAIL

    recipients = [admin_email] # Always send to admin
    if booking.customer.email:
        recipients.append(booking.customer.email)

    if not recipients:
        print(f"No recipients found for booking {booking.booking_code} email.")
        return False # No one to send to

    try:
        pdf_bytes = generate_pdf_bytes(booking)
        email = EmailMessage(
            subject,
            body,
            from_email,
            recipients,
        )
        email.attach(f"receipt_{booking.booking_code}.pdf", pdf_bytes, "application/pdf")
        email.send()
        print(f"Email sent successfully for booking {booking.booking_code} to {recipients}")
        return True
    except Exception as e:
        print(f"Error sending email for booking {booking.booking_code}: {e}")
        return False


