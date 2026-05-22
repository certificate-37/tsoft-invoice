from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
import json
from invoice import generate_invoice

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Create invoices directory if it doesn't exist
INVOICES_DIR = os.path.join(os.path.dirname(__file__), 'invoices')
os.makedirs(INVOICES_DIR, exist_ok=True)

# Store invoice metadata in a JSON file (persists between restarts)
METADATA_FILE = os.path.join(os.path.dirname(__file__), 'invoices_metadata.json')

def load_metadata():
    """Load invoice metadata from JSON file"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    """Save invoice metadata to JSON file"""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

# Load existing invoices
invoices_db = load_metadata()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/create-invoice', methods=['POST'])
def create_invoice():
    try:
        data = request.json
        
        # Generate unique invoice ID
        invoice_id = len(invoices_db) + 1
        
        # Generate PDF
        file_path = generate_invoice(
            invoice_id=invoice_id,
            client=data['client'],
            items=data['items'],
            total=data['total']
        )
        
        # Store invoice metadata
        invoices_db[str(invoice_id)] = {
            'id': invoice_id,
            'client': data['client'],
            'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'total': data['total'],
            'items': data['items'],
            'file_path': file_path
        }
        
        # Save to JSON file
        save_metadata(invoices_db)
        
        return jsonify({
            'success': True,
            'invoice_id': invoice_id,
            'file_path': f'/api/download-invoice/{invoice_id}'
        })
    except Exception as e:
        app.logger.error(f"Error creating invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-invoice/<int:invoice_id>')
def download_invoice(invoice_id):
    invoice = invoices_db.get(str(invoice_id))
    if invoice and os.path.exists(invoice['file_path']):
        return send_file(
            invoice['file_path'],
            as_attachment=True,
            download_name=f'facture_{invoice_id}.pdf'
        )
    return jsonify({'error': 'Facture non trouvée'}), 404

@app.route('/api/invoices')
def get_invoices():
    return jsonify(list(invoices_db.values()))

@app.route('/api/invoice/<int:invoice_id>')
def get_invoice(invoice_id):
    invoice = invoices_db.get(str(invoice_id))
    if invoice:
        return jsonify(invoice)
    return jsonify({'error': 'Facture non trouvée'}), 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))