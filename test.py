from invoice import generate_invoice

file = generate_invoice(
    invoice_id=1,
    client="Ahmed",
    service="Website Design",
    price=50000
)

print("Generated:", file)