#!/usr/bin/env python3
"""
Webb-baserat verktyg för att analysera förändringar mellan Current och Proposed värden i Excel-filer
Vercel-compatible version
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import pandas as pd
import os
import uuid
from werkzeug.utils import secure_filename
from typing import List, Tuple, Dict
import io
import base64
import tempfile

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max filstorlek

# Use temporary directories for Vercel
UPLOAD_FOLDER = '/tmp/uploads'
RESULTS_FOLDER = '/tmp/results'
for folder in [UPLOAD_FOLDER, RESULTS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def find_current_proposed_pairs(df: pd.DataFrame) -> List[Tuple[str, str, str]]:
    """Hittar alla matchande Current/Proposed kolumnpar"""
    current_cols = [col for col in df.columns if ' - Current' in col]
    
    pairs = []
    for current_col in current_cols:
        base_name = current_col.replace(' - Current', '')
        proposed_col = base_name + ' - Proposed'
        if proposed_col in df.columns:
            pairs.append((base_name, current_col, proposed_col))
    
    # Hantera speciella fall
    special_cases = [
        ('Hourly Rate', 'Hourly Rate Current - Amount', 'Hourly Rate Proposed - Amount'),
        ('Manager(s)', 'Manager(s) - Current', 'Manager(s) - Proposed')
    ]
    
    for base_name, current_col, proposed_col in special_cases:
        if current_col in df.columns and proposed_col in df.columns:
            if (base_name, current_col, proposed_col) not in pairs:
                pairs.append((base_name, current_col, proposed_col))
    
    return sorted(pairs)

def analyze_changes(df: pd.DataFrame, pairs: List[Tuple[str, str, str]]) -> Dict:
    """Analyserar förändringar för varje rad och kolumnpar"""
    changes = {
        'summary': {},
        'details': [],
        'total_employees': len(df),
        'employees_with_changes': 0,
        'pairs': pairs
    }
    
    for index, row in df.iterrows():
        employee_changes = {
            'row_index': index + 1,
            'employee_id': row.get('Employee ID', 'N/A'),
            'worker': row.get('Worker', 'N/A'),
            'changes': []
        }
        
        for base_name, current_col, proposed_col in pairs:
            current_val = row[current_col] if pd.notna(row[current_col]) else ''
            proposed_val = row[proposed_col] if pd.notna(row[proposed_col]) else ''
            
            current_str = str(current_val).strip()
            proposed_str = str(proposed_val).strip()
            
            if current_str == 'nan':
                current_str = ''
            if proposed_str == 'nan':
                proposed_str = ''
            
            if current_str != proposed_str and proposed_str != '':
                change = {
                    'field': base_name,
                    'current': current_str if current_str else '(tomt)',
                    'proposed': proposed_str
                }
                employee_changes['changes'].append(change)
                
                if base_name not in changes['summary']:
                    changes['summary'][base_name] = 0
                changes['summary'][base_name] += 1
        
        if employee_changes['changes']:
            changes['details'].append(employee_changes)
    
    changes['employees_with_changes'] = len(changes['details'])
    return changes

def create_results_file(changes: Dict, df: pd.DataFrame, original_filename: str) -> str:
    """Skapar resultat Excel-fil och returnerar filnamnet"""
    summary_data = []
    
    for employee in changes['details']:
        for change in employee['changes']:
            summary_data.append({
                'Rad': employee['row_index'],
                'Anställd': employee['worker'],
                'Employee ID': employee['employee_id'],
                'Fält': change['field'],
                'Nuvarande värde': change['current'],
                'Föreslaget värde': change['proposed']
            })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # Skapa unikt filnamn
        base_name = os.path.splitext(original_filename)[0]
        unique_id = str(uuid.uuid4())[:8]
        output_file = f"{base_name}_analysis_{unique_id}.xlsx"
        output_path = os.path.join(app.config['RESULTS_FOLDER'], output_file)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Förändringar', index=False)
            df.to_excel(writer, sheet_name='Original Data', index=False)
            
            # Statistik
            stats_data = {
                'Statistik': ['Totalt antal anställda', 'Anställda med förändringar', 'Anställda utan förändringar'],
                'Antal': [changes['total_employees'], changes['employees_with_changes'], 
                         changes['total_employees'] - changes['employees_with_changes']]
            }
            
            field_stats = []
            for field, count in sorted(changes['summary'].items(), key=lambda x: x[1], reverse=True):
                field_stats.append({'Fält': field, 'Antal förändringar': count})
            
            if field_stats:
                stats_df = pd.DataFrame(stats_data)
                field_stats_df = pd.DataFrame(field_stats)
                
                stats_df.to_excel(writer, sheet_name='Statistik', index=False, startrow=0)
                field_stats_df.to_excel(writer, sheet_name='Statistik', index=False, startrow=len(stats_df) + 3)
        
        return output_file
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Ingen fil vald', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Ingen fil vald', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Analysera filen
            df = pd.read_excel(filepath)
            pairs = find_current_proposed_pairs(df)
            
            if not pairs:
                flash('Inga Current/Proposed kolumnpar hittades i filen!', 'error')
                os.remove(filepath)
                return redirect(url_for('index'))
            
            changes = analyze_changes(df, pairs)
            
            # Skapa resultatfil
            result_filename = create_results_file(changes, df, filename)
            
            # Rensa upp uppladdad fil
            os.remove(filepath)
            
            return render_template('results.html', 
                                 changes=changes, 
                                 original_filename=filename,
                                 result_filename=result_filename)
            
        except Exception as e:
            flash(f'Fel vid analys av filen: {str(e)}', 'error')
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return redirect(url_for('index'))
    
    else:
        flash('Endast .xlsx och .xls filer är tillåtna', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('Filen kunde inte hittas', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Kunde inte ladda ned filen: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    flash('Filen är för stor. Maximal filstorlek är 16MB.', 'error')
    return redirect(url_for('index'))

# This is the WSGI application for Vercel
def handler(event, context):
    return app

if __name__ == '__main__':
    app.run(debug=True) 