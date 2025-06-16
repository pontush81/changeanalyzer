#!/usr/bin/env python3
"""
Verktyg för att analysera förändringar mellan Current och Proposed värden i Excel-fil
"""

import pandas as pd
import sys
from typing import List, Tuple, Dict
import os

def analyze_excel_changes(file_path: str) -> None:
    """
    Analyserar en Excel-fil och visar alla förändringar mellan Current och Proposed värden
    """
    try:
        # Läs Excel-filen
        print(f"Läser Excel-fil: {file_path}")
        df = pd.read_excel(file_path)
        print(f"✓ Läste {len(df)} rader och {len(df.columns)} kolumner")
        
        # Identifiera alla Current/Proposed par
        pairs = find_current_proposed_pairs(df)
        print(f"✓ Hittade {len(pairs)} Current/Proposed par")
        
        if not pairs:
            print("Inga Current/Proposed par hittades!")
            return
        
        # Visa identifierade par
        print("\n📋 IDENTIFIERADE KOLUMNPAR:")
        for i, (base_name, current_col, proposed_col) in enumerate(pairs, 1):
            print(f"  {i:2d}. {base_name}")
        
        # Analysera förändringar
        changes = analyze_changes(df, pairs)
        
        # Visa resultaten
        display_results(changes, df)
        
        # Spara till ny Excel-fil
        save_results(changes, df, pairs, file_path)
        
    except Exception as e:
        print(f"❌ Fel: {e}")
        sys.exit(1)

def find_current_proposed_pairs(df: pd.DataFrame) -> List[Tuple[str, str, str]]:
    """
    Hittar alla matchande Current/Proposed kolumnpar
    Returnerar: Lista med (base_name, current_col, proposed_col)
    """
    current_cols = [col for col in df.columns if ' - Current' in col]
    proposed_cols = [col for col in df.columns if ' - Proposed' in col]
    
    pairs = []
    for current_col in current_cols:
        base_name = current_col.replace(' - Current', '')
        proposed_col = base_name + ' - Proposed'
        if proposed_col in df.columns:
            pairs.append((base_name, current_col, proposed_col))
    
    # Hantera speciella fall som "Hourly Rate Current - Amount"
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
    """
    Analyserar förändringar för varje rad och kolumnpar
    """
    changes = {
        'summary': {},
        'details': [],
        'total_employees': len(df),
        'employees_with_changes': 0
    }
    
    for index, row in df.iterrows():
        employee_changes = {
            'row_index': index + 1,  # Excel använder 1-baserad indexering
            'employee_id': row.get('Employee ID', 'N/A'),
            'worker': row.get('Worker', 'N/A'),
            'changes': []
        }
        
        for base_name, current_col, proposed_col in pairs:
            current_val = row[current_col] if pd.notna(row[current_col]) else ''
            proposed_val = row[proposed_col] if pd.notna(row[proposed_col]) else ''
            
            # Konvertera till strängar för jämförelse
            current_str = str(current_val).strip()
            proposed_str = str(proposed_val).strip()
            
            # Ignorera NaN och tomma värden i jämförelsen
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
                
                # Uppdatera sammanfattning
                if base_name not in changes['summary']:
                    changes['summary'][base_name] = 0
                changes['summary'][base_name] += 1
        
        if employee_changes['changes']:
            changes['details'].append(employee_changes)
    
    changes['employees_with_changes'] = len(changes['details'])
    return changes

def display_results(changes: Dict, df: pd.DataFrame) -> None:
    """
    Visar resultaten i terminalen
    """
    print("\n" + "="*60)
    print("📊 SAMMANFATTNING AV FÖRÄNDRINGAR")
    print("="*60)
    
    print(f"Totalt antal anställda: {changes['total_employees']}")
    print(f"Anställda med förändringar: {changes['employees_with_changes']}")
    print(f"Anställda utan förändringar: {changes['total_employees'] - changes['employees_with_changes']}")
    
    if changes['summary']:
        print(f"\n📈 FÖRÄNDRINGAR PER FÄLT:")
        for field, count in sorted(changes['summary'].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {field}: {count} förändringar")
    
    print("\n" + "="*60)
    print("📋 DETALJERADE FÖRÄNDRINGAR")
    print("="*60)
    
    if not changes['details']:
        print("🎉 Inga förändringar hittades!")
        return
    
    for employee in changes['details']:
        print(f"\n👤 Rad {employee['row_index']}: {employee['worker']} (ID: {employee['employee_id']})")
        for change in employee['changes']:
            print(f"   🔄 {change['field']}:")
            print(f"      Nuvarande: '{change['current']}'")
            print(f"      Föreslaget: '{change['proposed']}'")

def save_results(changes: Dict, df: pd.DataFrame, pairs: List[Tuple[str, str, str]], original_file: str) -> None:
    """
    Sparar resultaten till en ny Excel-fil
    """
    # Skapa en sammanfattning som DataFrame
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
        
        # Skapa filnamn för resultatfilen
        base_name = os.path.splitext(os.path.basename(original_file))[0]
        output_file = f"{base_name}_changes_analysis.xlsx"
        
        # Skriv till Excel med flera sheets
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Sammanfattning av förändringar
            summary_df.to_excel(writer, sheet_name='Förändringar', index=False)
            
            # Sheet 2: Original data
            df.to_excel(writer, sheet_name='Original Data', index=False)
            
            # Sheet 3: Statistik
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
        
        print(f"\n💾 Resultat sparade i: {output_file}")
    else:
        print("\n💾 Inga förändringar att spara.")

def main():
    """
    Huvudfunktion
    """
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = '/Users/pontus.horberg-Local/Downloads/testfil.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ Filen hittades inte: {file_path}")
        sys.exit(1)
    
    print("🔍 Excel Change Analyzer")
    print("=" * 40)
    
    analyze_excel_changes(file_path)
    
    print("\n✅ Analys klar!")

if __name__ == "__main__":
    main() 