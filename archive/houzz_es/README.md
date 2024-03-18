# Web Scraper for Company Data

This Python script is designed to scrape company data from websites and write this information to a CSV file. The URLs of the companies' websites are read from another CSV file.

## Features

The script extracts the following information:

1. Company's URL.
2. Company's Name.
3. Company's Website.
4. Company's Telephone Number.
5. Full Company Address, including Street, Locality, Region, Postal Code, and Country.
6. All emails found on the main site and its links.
7. Whether certain keywords (Commercial, Residential, LEED, Greengaurd, Phthalates, Polyvinyl, PVC) are present in the website's text.

## Requirements

The script uses the following Python libraries:

- `requests`
- `BeautifulSoup` from `bs4`
- `json`
- `re`
- `csv`
- `urllib.parse`

Before running the script, make sure to install these libraries using pip:

```bash
pip install -r requirements.txt
beautifulsoup4==4.11.2
Requests==2.31.0
selenium==4.10.0
lxml==4.9.3