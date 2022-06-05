from bs4 import BeautifulSoup
from requests_html import HTMLSession
import requests, schedule
import sys, os, socket, time, datetime

base_date = datetime.datetime.strptime(os.getenv("BASE_DATE"), '%Y-%m-%d')
pods = 32
service_host = os.getenv("SERVICE_HOST")
service_port = int(os.getenv("SERVICE_PORT"))

class UrlGenerator():
    def __init__(self):
        self.url = 'https://www.google.com/search?q='

    # Google search with queries and parameters
    def google_search(self, query, time='qdr:d', num=100):
        search_url = self.url + query + \
            '&tbm=nws&tbs=%s&num=%d&lr=lang_en' % (time, num)
        response = self.get_source(search_url)
        return self.parse_googleResults(response)

    def get_source(self, url):
        try:
            session = HTMLSession()
            response = session.get(url)
            return response
        except requests.exceptions.RequestException as e:
            print(e, file=sys.stderr)
            return None

    # Google Search Result Parsing
    def parse_googleResults(self, response):
        css_identifier_link = "WlydOe"
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.findAll("a", {"class": css_identifier_link})
        return [link['href'] for link in links]

    def generate_url(self, date, query, num=100):
        search_time = self.get_google_search_date(date)
        return self.google_search(query, time=search_time, num=num)

    def get_google_search_date(self, date):
        return 'cdr%3A1%2Ccd_min%3A{month}%2F{day}%2F{year}%2Ccd_max%3A{month}%2F{day}%2F{year}'.format(
            month=date.month, day=date.day, year=date.year
        )

# Get Current Time (UTC+8)
def cur_time_str():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')

def send_links(links, date):
    try:
        print('[%s] Sending links to %s:%d' % (cur_time_str(), service_host, service_port))
        for link in links:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((service_host, service_port))
            outstr = date.strftime('%Y-%m-%d') + ' ' + link + '\n'
            sock.sendall(outstr.encode('ascii'))
            sock.close()
        print('[%s] Sent %d link(s)' % (cur_time_str(), len(links)))
    except socket.error as e:
        print(e, file=sys.stderr)
        os._exit(1)

def search_tsmc():
    global base_date
    print('[%s] TSMC @ %s' % (cur_time_str(), base_date.strftime('%Y-%m-%d')))
    generator = UrlGenerator()
    links = generator.generate_url(base_date, 'TSMC', num=100)
    send_links(links, base_date)

def search_asml():
    global base_date
    print('[%s] ASML @ %s' % (cur_time_str(), base_date.strftime('%Y-%m-%d')))
    generator = UrlGenerator()
    links = generator.generate_url(base_date, 'ASML', num=100)
    send_links(links, base_date)

def search_applmat():
    global base_date
    print('[%s] APPLIED @ %s' % (cur_time_str(), base_date.strftime('%Y-%m-%d')))
    generator = UrlGenerator()
    links = generator.generate_url(base_date, 'Applied+Materials', num=100)
    send_links(links, base_date)

def search_sumco():
    global base_date
    print('[%s] SUMCO @ %s' % (cur_time_str(), base_date.strftime('%Y-%m-%d')))
    generator = UrlGenerator()
    links = generator.generate_url(base_date, 'SUMCO', num=100)
    send_links(links, base_date)

@schedule.repeat(schedule.every(32).minutes)
def search():
    search_tsmc()
    time.sleep(475)
    search_asml()
    time.sleep(475)
    search_applmat()
    time.sleep(475)
    search_sumco()
    global base_date
    base_date = base_date - datetime.timedelta(days=pods)

if __name__ == '__main__':
    # Initial Job
    search()

    # Check schedule
    while True:
        schedule.run_pending()
        time.sleep(120)