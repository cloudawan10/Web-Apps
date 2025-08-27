import os
import csv
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import openai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'kode-kunci'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  #ukuran maks file yang dapat diupload

# Konfigurasi OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Fungsi untuk memvalidasi dan memproses file CSV
def process_csv(file):
    data = {
        'dates': [],
        'inflation': [],
        'interest_rates': [],
        'foreign_reserves': [],
        'transactions': []
    }
    
    # Membaca file CSV
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    baca_csv = csv.DictReader(stream)
    
    for row in baca_csv:
        if 'date' in row:
            data['dates'].append(row['date'])
        elif 'tanggal' in row:
            data['dates'].append(row['tanggal'])
        else:
            data['dates'].append(str(len(data['dates']) + 1))
            
        if 'inflasi' in row:
            data['inflation'].append(float(row['inflasi']))
        elif 'inflation' in row:
            data['inflation'].append(float(row['inflation']))
            
        if 'suku_bunga' in row:
            data['interest_rates'].append(float(row['suku_bunga']))
        elif 'interest_rate' in row:
            data['interest_rates'].append(float(row['interest_rate']))
            
        if 'cadangan_devisa' in row:
            data['foreign_reserves'].append(float(row['cadangan_devisa']))
        elif 'foreign_reserves' in row:
            data['foreign_reserves'].append(float(row['foreign_reserves']))
            
        if 'transaksi' in row:
            data['transactions'].append(float(row['transaksi']))
        elif 'transactions' in row:
            data['transactions'].append(float(row['transactions']))
    
    return data

# Fungsi untuk membuat dan menampilkan grafik
def create_charts(data):
    charts = {}
    
    # Grafik garis untuk inflasi dan suku bunga
    if data['inflation'] and data['interest_rates']:
        plt.figure(figsize=(10, 6))
        plt.plot(data['dates'], data['inflation'], marker='o', label='Inflasi')
        plt.plot(data['dates'], data['interest_rates'], marker='s', label='Suku Bunga')
        plt.title('Tren Inflasi dan Suku Bunga')
        plt.xlabel('Periode')
        plt.ylabel('Persentase')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        
        # Lakukan Proses Encode grafik ke base64
        charts['trend_chart'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
    
    # Grafik batang untuk cadangan devisa dan transaksi
    if data['foreign_reserves'] and data['transactions']:
        plt.figure(figsize=(10, 6))
        
        max_foreign = max(data['foreign_reserves']) if data['foreign_reserves'] else 1
        max_transactions = max(data['transactions']) if data['transactions'] else 1
        scale_factor = max_foreign / max_transactions if max_transactions != 0 else 1
        
        scaled_transactions = [t * scale_factor for t in data['transactions']]
        
        x = range(len(data['dates']))
        width = 0.35
        
        plt.bar([i - width/2 for i in x], data['foreign_reserves'], width, label='Cadangan Devisa')
        plt.bar([i + width/2 for i in x], scaled_transactions, width, label='Transaksi (skala disesuaikan)')
        plt.title('Cadangan Devisa dan Transaksi')
        plt.xlabel('Periode')
        plt.ylabel('Nilai')
        plt.xticks(x, data['dates'], rotation=45)
        plt.legend()
        plt.grid(True, axis='y')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        
        charts['bar_chart'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
    
    return charts

# Fungsi untuk menganalisis teks dengan OpenAI
def analyze_text(text):
    try:
        prompt = f"""
        Ringkas dan jelaskan isi laporan ini secara singkat untuk manajemen Bank Indonesia.
                
        Laporan:
        {text}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Analisis Ekonomi."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error dalam menganalisis teks: {str(e)}"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(request.url)
    
    if file:
        filename = file.filename
        file_ext = filename.split('.')[-1].lower()
        
        if file_ext == 'csv':
            try:
                data = process_csv(file)
                charts = create_charts(data)
                
                # Simpan data dalam session untuk ditampilkan di dashboard
                return render_template('dashboard.html', data=data, charts=charts, analysis=None)
            except Exception as e:
                flash(f'Error memproses file CSV: {str(e)}', 'danger')
                return redirect(url_for('index'))
                
        elif file_ext == 'txt':
            try:
                text_content = file.read().decode('utf-8')
                analysis = analyze_text(text_content)
                return render_template('dashboard.html', data=None, charts=None, analysis=analysis, text_content=text_content)
            except Exception as e:
                flash(f'Error memproses file teks: {str(e)}', 'danger')
                return redirect(url_for('index'))
        else:
            flash('Format file tidak didukung. Harap upload file dalam format CSV atau TXT.', 'danger')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)