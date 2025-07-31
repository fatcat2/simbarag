from bs4 import BeautifulSoup
import chromadb
import httpx

client = chromadb.PersistentClient(path="/Users/ryanchen/Programs/raggr/chromadb")

# Scrape
BASE_URL = "https://www.vet.cornell.edu"
LIST_URL = "/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics"

QUERY_URL = BASE_URL + LIST_URL
r = httpx.get(QUERY_URL)
soup = BeautifulSoup(r.text)

container = soup.find("div", class_="field-body")
a_s = container.find_all("a", href=True)

new_texts = []

for link in a_s:
    endpoint = link["href"]
    query_url = BASE_URL + endpoint
    r2 = httpx.get(query_url)
    article_soup = BeautifulSoup(r2.text)
