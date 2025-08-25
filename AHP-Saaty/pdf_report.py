from typing import Dict, List
from fpdf import FPDF

class MinimalReport(FPDF):
    def header(self):
        # sin líneas/ornamentos; título centrado
        self.set_font("Open Sans", "B", 14)
        self.cell(0, 10, "Informe de Criticidad", ln=True, align="C")
        self.ln(2)

def build_pdf(path_out: str, meta: Dict[str, str], categoria: str, ic: float, explicacion: str):
    """
    Crea un PDF mínimo SOLO con:
      - Recinto, Activo, Situación, (y cualquier otra clave/meta)
      - Nivel de criticidad (IC + categoría)
      - Explicación técnica breve
    """
    pdf = MinimalReport(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Open Sans", "", 11)

    # Sección de contexto (meta)
    for k, v in meta.items():
        if v is None: 
            continue
        pdf.set_font("Open Sans", "B", 11); pdf.cell(35, 7, f"{k}:", ln=0)
        pdf.set_font("Open Sans", "", 11);  pdf.multi_cell(0, 7, str(v))
    pdf.ln(2)

    # Nivel de criticidad
    pdf.set_font("Open Sans", "B", 11); pdf.cell(50, 7, "Nivel de criticidad:", ln=0)
    pdf.set_font("Open Sans", "", 11);  pdf.cell(0, 7, f"{categoria} (IC={ic:.2f})", ln=1)

    # Explicación
    pdf.ln(3)
    pdf.set_font("Open Sans", "B", 11); pdf.cell(0, 7, "Explicación técnica:", ln=1)
    pdf.set_font("Open Sans", "", 11)
    pdf.multi_cell(0, 6.5, explicacion)

    pdf.output(path_out)
