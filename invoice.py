from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVOICES_DIR = os.path.join(BASE_DIR, "invoices")
os.makedirs(INVOICES_DIR, exist_ok=True)


def format_number_fr(number):
    """
    Format number in French/Algerian format:
    - Space as thousand separator
    - Comma as decimal separator
    Example: 8500.50 -> "8 500,50"
    """
    if number is None:
        return "0,00"
    
    # Format with French locale
    return f"{number:,.2f}".replace(",", " ").replace(".", ",")


def generate_invoice(invoice_id, client, items, total):
    """
    Generate a PDF invoice
    
    Args:
        invoice_id: Unique invoice number
        client: Client name
        items: List of items with name, qty, unit_price
        total: Total amount
    
    Returns:
        Path to generated PDF file
    """
    env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")))
    template = env.get_template("invoice.html")

    # Calculate subtotal for each item and format numbers
    for item in items:
        item['subtotal'] = item['qty'] * item['unit_price']
        # Add formatted versions for display
        item['unit_price_formatted'] = format_number_fr(item['unit_price'])
        item['subtotal_formatted'] = format_number_fr(item['subtotal'])

    html_content = template.render(
        invoice_id=invoice_id,
        date=datetime.now().strftime("%Y-%m-%d"),
        client=client,
        items=items,
        total=total,
        total_formatted=format_number_fr(total)
    )

    file_path = os.path.join(INVOICES_DIR, f"invoice_{invoice_id}.pdf")
    
    try:
        # FIXED: Correct way to call WeasyPrint HTML
        html = HTML(string=html_content, base_url=os.path.join(BASE_DIR, "templates"))
        html.write_pdf(file_path)
        return file_path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise


def get_invoice_path(invoice_id):
    """Get path of an invoice by ID"""
    file_path = os.path.join(INVOICES_DIR, f"invoice_{invoice_id}.pdf")
    if os.path.exists(file_path):
        return file_path
    return None