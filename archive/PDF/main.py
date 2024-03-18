import re
import pdfplumber


def extract_emails_from_pdf(file):
    pdf = pdfplumber.open(file)
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    emails = []

    for page in pdf.pages:
        text = page.extract_text()
        for match in re.finditer(email_pattern, text):
            emails.append(match.group())

    return emails


# Путь к вашему файлу
file = "140454.pdf"

emails = extract_emails_from_pdf(file)

for email in emails:
    print(email)
