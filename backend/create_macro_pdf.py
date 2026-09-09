from fpdf import FPDF

def create_pdf(path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    text = """
    India Macroeconomy Starter Dataset
    Reserve Bank of India Annual Report 2024-25
    
    Macroeconomic Performance:
    Real GDP growth moderated to 6.5 percent in 2024-25. However, India remained the fastest 
    growing major economy. Growth in gross value added (GVA) in the agriculture and allied 
    sector in 2024-25 stood at 4.6 per cent.
    
    Inflation Dynamics:
    Headline inflation moderated to an average of 4.6 per cent during 2024-25 from 5.4 per 
    cent in the previous year, largely driven by a moderation in core (CPI excluding food 
    and fuel) inflation to 3.5 per cent. Food inflation remained elevated at 6.7 per cent.
    
    External Sector:
    Net foreign direct investment (FDI) inflows stood at US$ 0.4 billion during 2024-25, 
    lower than US$ 10.1 billion a year ago.
    """
    for line in text.split('\n'):
        pdf.cell(200, 8, txt=line.strip(), ln=True, align='L')
    pdf.output(path)
    print(f"Created {path}")

if __name__ == "__main__":
    create_pdf("test_macro.pdf")
