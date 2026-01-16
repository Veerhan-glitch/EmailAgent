import PyPDF2

# Open and read the PDF file
with open('email_agent.pdf', 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    
    print(f"Total Pages: {len(pdf_reader.pages)}\n")
    print("="*80)
    
    # Extract text from each page
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        print(f"\n--- PAGE {page_num + 1} ---\n")
        print(text)
        print("\n" + "="*80)
