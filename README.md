# Excel Change Analyzer 📊

Ett webb-baserat verktyg för att analysera förändringar mellan "Current" och "Proposed" värden i Excel-filer. Perfekt för HR-system och personalförändringar.

![Excel Change Analyzer](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Flask](https://img.shields.io/badge/flask-latest-lightgrey)

## 🚀 Funktioner

- **Automatisk identifiering** av Current/Proposed kolumnpar
- **Snygg webbgränssnitt** med drag-and-drop filuppladdning
- **Detaljerad analys** som visar alla förändringar per person
- **Visuell presentation** av före/efter värden
- **Excel-export** av analysresultat
- **Mobilanpassad design**

## 📋 Vad verktyget gör

1. **Läser Excel-filer** med kolumner som följer mönstret "Kolumnnamn - Current" och "Kolumnnamn - Proposed"
2. **Identifierar automatiskt** alla matchande kolumnpar
3. **Jämför värden** och hittar alla förändringar
4. **Skapar rapport** som visar:
   - Totala antal anställda
   - Antal anställda med förändringar
   - Förändringar per fält (statistik)
   - Detaljerad genomgång per person
5. **Exporterar resultat** till ny Excel-fil med flera sheets

## 🛠️ Installation

### Förutsättningar
- Python 3.9 eller senare
- pip (Python Package Installer)

### Steg 1: Klona repot
```bash
git clone https://github.com/pontush81/changeanalyzer.git
cd changeanalyzer
```

### Steg 2: Installera beroenden
```bash
pip3 install -r requirements.txt
```

### Steg 3: Starta applikationen
```bash
python3 web_analyzer.py
```

### Steg 4: Öppna webbläsaren
Gå till: `http://localhost:5001`

## 📊 Användning

### Webb-gränssnitt
1. Öppna `http://localhost:5001` i din webbläsare
2. Dra och släpp din Excel-fil eller klicka för att välja fil
3. Klicka "Analysera Excel-fil"
4. Se resultaten direkt på webbsidan
5. Ladda ned detaljerad Excel-rapport

### Kommandoradsverktyg
```bash
python3 change_analyzer.py /sökväg/till/din/fil.xlsx
```

## 📁 Projektstruktur

```
changeanalyzer/
├── web_analyzer.py          # Flask webbapplikation
├── change_analyzer.py       # Kommandoradsverktyg
├── templates/
│   ├── index.html           # Startsida
│   └── results.html         # Resultatsida
├── uploads/                 # Temporära uppladdade filer
├── results/                 # Genererade rapporter
├── requirements.txt         # Python-beroenden
└── README.md               # Denna fil
```

## 🔧 Teknisk information

### Stödda filformat
- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)

### Kolumnformat som stöds
Verktyget letar automatiskt efter kolumnpar med dessa mönster:
- `Kolumnnamn - Current` och `Kolumnnamn - Proposed`
- `Manager(s) - Current` och `Manager(s) - Proposed`
- `Hourly Rate Current - Amount` och `Hourly Rate Proposed - Amount`

### Maximal filstorlek
- 16MB per fil

## 🛡️ Säkerhet

- Filer raderas automatiskt efter analys
- Ingen data sparas permanent på servern
- Endast Excel-filer accepteras
- Filstorleksbegränsning för säkerhet

## 🐛 Felsökning

### Port 5000 redan upptagen (macOS)
På macOS kan port 5000 användas av AirPlay. Applikationen använder port 5001 som standard.

### Installationsproblem
```bash
# Om openpyxl saknas
pip3 install openpyxl

# Om pandas saknas  
pip3 install pandas

# Om Flask saknas
pip3 install flask
```

## 📝 Exempel på Excel-struktur

Din Excel-fil bör ha kolumner som:
- `Position - Current` och `Position - Proposed`
- `Base Pay - Current` och `Base Pay - Proposed`
- `Manager(s) - Current` och `Manager(s) - Proposed`
- `Location - Current` och `Location - Proposed`

## 🤝 Bidrag

Bidrag är välkomna! Skapa gärna en issue eller pull request.

## 📄 Licens

MIT License - se LICENSE filen för detaljer.

## 👨‍💻 Utvecklare

Utvecklat av [pontush81](https://github.com/pontush81)

## 🔄 Versioner

- **v1.0.0** - Initial release med webb-gränssnitt och kommandoradsverktyg

---

**📧 Support:** Skapa en issue på GitHub för support och buggrapporter. 