import PyPDF2

# Specify the path to your PDF file
# pdf_file = 'Document.pdf'
def extract_text_from_pdf(pdf_file):

    # Open the PDF file in read-binary mode
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)

        # Extract text from each page
        full_text = ''
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            full_text += page_text
    print("extracted full text")
    return full_text


