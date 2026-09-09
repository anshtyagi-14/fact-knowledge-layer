from fpdf import FPDF
import os

def create_pdf(path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    text = """
    Delhivery Q4 FY24 Earnings Presentation
    
    Financial Highlights:
    FY24 revenue from services increased to Rs. 8,142 Cr, reflecting a YoY growth of 12.7%.
    FY24 EBITDA increased by Rs. 578 Cr to Rs. 127 Cr from Rs. (452 Cr) in FY23.
    Express parcel shipments grew to 740 Mn in FY24, representing an 11.5% YoY growth.
    
    Operating Metrics:
    Active customers reached 33,278 in Q4 FY24.
    Delhivery currently operates 111 gateways and 29 automated sort centers.
    The total team size is 63,713 as of March 31, 2024.
    """
    for line in text.split('\n'):
        pdf.cell(200, 10, txt=line.strip(), ln=True, align='L')
    pdf.output(path)
    print(f"Created {path}")

if __name__ == "__main__":
    create_pdf("test.pdf")
