import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from core.types import PatientData

def build_pdf(patient: PatientData, rows: list[list[str]]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Health Report")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Health Report</b>", styles["Title"]))
    pinfo = (
        f"<b>Patient:</b> {patient.name or '—'} &nbsp;&nbsp; "
        f"<b>Sex:</b> {patient.sex or '—'} &nbsp;&nbsp; "
        f"<b>Age:</b> {int(patient.age) if patient.age is not None else '—'}"
    )
    story.append(Paragraph(pinfo, styles["Normal"]))
    story.append(Spacer(1, 8))

    if rows:
        tbl = Table(
            [["Metric", "Value", "Interpretation"]] + rows,
            hAlign='LEFT',
            colWidths=[130, 100, 260]
        )
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eeeeee')),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fafafa')]),
        ]))
        story.append(tbl)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Disclaimer:</b> Screening & education only; not medical advice.",
        styles['Italic']
    ))

    doc.build(story)
    return buf.getvalue()