import os
import io
import csv
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from werkzeug.exceptions import RequestEntityTooLarge

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # Ukuran file maks 8 MB

# Konfigurasi OpenAI API
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Fungsi untuk memproses file CSV dengan pandas
def process_csv(file):
    try:
        # Membaca file CSV dengan pandas
        df = pd.read_csv(file)
        
        # Cek jika DataFrame kosong
        if df.empty:
            return None, "File CSV kosong. Tidak ada data untuk diproses."
        
        df.columns = df.columns.str.strip().str.lower()
        
        date_columns = ['date', 'tanggal', 'period', 'periode', 'bulan', 'tahun']
        inflation_columns = ['inflasi', 'inflation']
        interest_columns = ['suku_bunga', 'interest_rate', 'bunga']
        reserves_columns = ['cadangan_devisa', 'foreign_reserves', 'devisa']
        transactions_columns = ['transaksi', 'transactions', 'volume']
        
        def get_first_available_column(possible_columns):
            for col in possible_columns:
                if col in df.columns:
                    return col
            return None
        
        date_col = get_first_available_column(date_columns)
        inflation_col = get_first_available_column(inflation_columns)
        interest_col = get_first_available_column(interest_columns)
        reserves_col = get_first_available_column(reserves_columns)
        transactions_col = get_first_available_column(transactions_columns)
        
        if date_col:
            dates = df[date_col].fillna('').astype(str).tolist()
        else:
            dates = [f"Periode {i+1}" for i in range(len(df))]
        
        def get_numeric_data(column_name, default_value=0.0):
            if column_name and column_name in df.columns:
                return df[column_name].fillna(default_value).astype(float).tolist()
            return [default_value] * len(dates)
        
        inflation = get_numeric_data(inflation_col)
        interest = get_numeric_data(interest_col)
        reserves = get_numeric_data(reserves_col)
        transactions = get_numeric_data(transactions_col)
        
        data = {
            'dates': dates,
            'inflation': inflation,
            'interest_rates': interest,
            'foreign_reserves': reserves,
            'transactions': transactions,
            'columns_found': {
                'date': date_col,
                'inflation': inflation_col,
                'interest': interest_col,
                'reserves': reserves_col,
                'transactions': transactions_col
            }
        }
        
        return data, None
        
    except pd.errors.EmptyDataError:
        return None, "File CSV kosong atau tidak valid."
    except pd.errors.ParserError:
        return None, "Error parsing CSV. Pastikan format file benar."
    except Exception as e:
        return None, f"Error processing CSV: {str(e)}"

# Fungsi untuk membuat dan menampilkan grafik
def create_charts(data):
    charts = {}
    
    # Grafik garis untuk menampilkan data inflasi dan suku bunga
    if any(x != 0 for x in data['inflation']) or any(x != 0 for x in data['interest_rates']):
        plt.figure(figsize=(10, 6))
        
        if any(x != 0 for x in data['inflation']):
            plt.plot(data['dates'], data['inflation'], marker='o', color='blue', label='Inflasi', linewidth=2)
        
        if any(x != 0 for x in data['interest_rates']):
            plt.plot(data['dates'], data['interest_rates'], marker='s', color='red', label='Suku Bunga', linewidth=2)
        
        plt.title('Tren Inflasi dan Suku Bunga')
        plt.xlabel('Periode')
        plt.ylabel('Persentase')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        charts['trend_chart'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
    
    # Menampilkan grafik batang untuk cadangan devisa dan transaksi
    if any(x != 0 for x in data['foreign_reserves']) or any(x != 0 for x in data['transactions']):
        plt.figure(figsize=(10, 6))
        
        max_foreign = max(data['foreign_reserves']) if any(x != 0 for x in data['foreign_reserves']) else 1
        max_transactions = max(data['transactions']) if any(x != 0 for x in data['transactions']) else 1
        scale_factor = max_foreign / max_transactions if max_transactions != 0 else 1
        
        scaled_transactions = [t * scale_factor for t in data['transactions']]
        
        x = range(len(data['dates']))
        width = 0.35
        
        if any(x != 0 for x in data['foreign_reserves']):
            plt.bar([i - width/2 for i in x], data['foreign_reserves'], width, 
                   label='Cadangan Devisa', color='orange', alpha=0.8)
        
        if any(x != 0 for x in data['transactions']):
            plt.bar([i + width/2 for i in x], scaled_transactions, width, 
                   label='Transaksi (skala disesuaikan)', color='green', alpha=0.8)
        
        plt.title('Cadangan Devisa dan Transaksi')
        plt.xlabel('Periode')
        plt.ylabel('Nilai')
        plt.xticks(x, data['dates'], rotation=45)
        plt.legend()
        plt.grid(True, axis='y', alpha=0.3)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        charts['bar_chart'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
    
    return charts

# Fungsi untuk menganalisis data teks dengan OpenAI
def analyze_text(text):
    try:
        # Batasi teks untuk menghindari token berlebih
        if len(text) > 10000:
            text = text[:10000] + "... [teks dipotong untuk analisis]"
            
        prompt = f"""
        Ringkas dan jelaskan isi laporan ini secara singkat untuk manajemen Bank Indonesia.
        Berikan ringkasan 3-5 kalimat dan insight penting atau rekomendasi.

        Laporan:
        {text}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Anda adalah analis ekonomi senior di Bank Indonesia. Berikan analisis yang jelas dan ringkas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error dalam menganalisis teks: {str(e)}"

@app.route('/')
def index():
    # Clear previous session data
    session.pop('csv_data', None)
    session.pop('csv_charts', None)
    session.pop('text_content', None)
    session.pop('text_analysis', None)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            flash('Tidak ada file yang dipilih', 'danger')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Tidak ada file yang dipilih', 'danger')
            return redirect(url_for('index'))
        
        if file:
            filename = file.filename
            file_ext = filename.split('.')[-1].lower()
            
            if file_ext == 'csv':
                data, error = process_csv(file)
                
                if error:
                    flash(error, 'danger')
                    return redirect(url_for('index'))
                
                charts = create_charts(data)
                
                session['csv_data'] = data
                session['csv_charts'] = charts
                
                return render_template('dashboard.html', data=data, charts=charts, 
                                     analysis=None, text_content=None, 
                                     now=datetime.now().strftime("%d %B %Y %H:%M"))
                
            elif file_ext == 'txt':
                # Batasi ukuran file teks
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                
                if size > 500000:  # 500KB max
                    flash('File teks terlalu besar. Maksimal 500KB.', 'danger')
                    return redirect(url_for('index'))
                
                text_content = file.read().decode('utf-8')
                
                # Cek jika file kosong
                if not text_content.strip():
                    flash('File teks kosong.', 'danger')
                    return redirect(url_for('index'))
                
                analysis = analyze_text(text_content)
                
                # Simpan data dalam session
                session['text_content'] = text_content
                session['text_analysis'] = analysis
                
                return render_template('dashboard.html', data=None, charts=None, 
                                     analysis=analysis, text_content=text_content,
                                     now=datetime.now().strftime("%d %B %Y %H:%M"))
            else:
                flash('Format file tidak didukung. Harap unggah file CSV atau TXT.', 'danger')
                return redirect(url_for('index'))
                
    except RequestEntityTooLarge:
        flash('File terlalu besar. Maksimal 8MB.', 'danger')
        return redirect(url_for('index'))
    except UnicodeDecodeError:
        flash('Error membaca file. Pastikan file dalam format yang benar.', 'danger')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error memproses file: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    return redirect(url_for('index'))

# Error handler untuk file terlalu besar
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash('File terlalu besar. Maksimal 8MB.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", False))