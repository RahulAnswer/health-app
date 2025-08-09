Health Analyzer (Streamlit)
A modular Streamlit app that reads lab reports (PDF or manual input) and generates a one‑page PDF with liver scores:
FLI, FIB‑4, APRI, NFS, plus a Liver Health (0–100) composite with interpretations.

Features
Upload a text‑based lab PDF (beta) → auto‑fill fields (name/sex/age + labs).

Manual overrides for all inputs.

Computes FLI, FIB‑4, APRI, NFS with clear risk bands.

Exports a consolidated PDF report.

Modular architecture → add/remove health modules without touching app.py.

Repo structure
arduino
Copy
Edit
.
├─ app.py
├─ config.toml
├─ requirements.txt
├─ core/
│  ├─ pdf_parser.py
│  ├─ registry.py
│  ├─ report.py
│  ├─ types.py
│  └─ utils.py
└─ modules/
   └─ liver/
      ├─ liver.py
      ├─ scores.py
      └─ __init__.py
If your files aren’t already under modules/liver/, please move them to match the above (the loader expects modules.{name}.{name}).

Quickstart (local)
Create & activate venv

bash
Copy
Edit
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
Install deps

bash
Copy
Edit
pip install -r requirements.txt
Run

bash
Copy
Edit
streamlit run app.py
Open the local URL shown by Streamlit (usually http://localhost:8501).

Deploy on Streamlit Community Cloud (free)
Push this project to GitHub (include all files above).

Go to share.streamlit.io → New app → pick your repo/branch → main file: app.py.

Click Deploy. You’ll get a public link like:

php-template
Copy
Edit
https://<your-username>-<repo>.streamlit.app
Hugging Face Spaces (alternative, free)
Create a new Space → template Streamlit → upload the same files → it builds and gives you a public URL.

Configuration
config.toml controls which modules load and their order:

toml
Copy
Edit
[modules.liver]
enabled = true
order = 1
Add more modules under [modules.<name>] and place code in modules/<name>/<name>.py.

Using the app
Upload Lab PDF (optional): Works for text‑based PDFs (not scans). The parser detects:

Patient name/sex/age

AST, ALT, GGT, Triglycerides, Platelets, Albumin

ULN AST (reads the upper value from ranges like 3 – 35).

Edit fields if anything looks off.

Click Download PDF Report for a shareable, printable summary.

Adding a new health module
Create modules/my_module/my_module.py.

Export id, title, and functions: inputs(data), compute(data), render(results), to_pdf(results).

Enable in config.toml:

toml
Copy
Edit
[modules.my_module]
enabled = true
order = 2
Formulas (implemented in modules/liver/scores.py)
FLI: Bedogni et al. logistic model (TG, BMI, GGT, waist).

FIB‑4: (Age × AST) / (Platelets × √ALT).

APRI: ((AST / ULN_AST) × 100) / Platelets.

NFS: −1.675 + 0.037×Age + 0.094×BMI + 1.13×Diab + 0.99×(AST/ALT) − 0.013×Platelets − 0.66×Albumin.

Liver Health (0–100): weighted subscores from FIB‑4/APRI/NFS.

Troubleshooting
Blank PDF fields / wrong ULN AST: Your lab PDF must be text‑based. For scanned PDFs, type values manually. ULN AST parsing prefers the upper bound of the AST reference range; you can override it in the UI.

NameError: io not defined: Ensure core/report.py begins with import io.

PDF upload fails: Confirm pdfplumber is installed and the file is not a scan.

Python version: Streamlit works best on 3.10–3.12. (3.13 is new; if you see dependency issues, try 3.12.)

Privacy
All processing happens in your session. Do not upload personally identifiable data unless you have consent.

License: Private/Proprietary (update as needed).
