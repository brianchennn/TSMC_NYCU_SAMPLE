from bs4 import BeautifulSoup
from requests_html import HTMLSession
import requests, schedule
import sys, os, socket, time, datetime

service_host = os.getenv("SERVICE_HOST")
service_port = int(os.getenv("SERVICE_PORT"))
#service_host = "140.113.68.204"
#service_host = "localhost"
#service_port = 7878

class UrlGenerator():
    def __init__(self):
        self.url = 'https://www.google.com/search?q='
        self.queries = ["TSMC", "Applied+Materials", "ASML", "SUMCO"]

    # Google search with queries and parameters
    def google_search(self, query, time='qdr:d', num=100, retry=5):
        search_url = self.url + query + \
            '&tbm=nws&tbs=%s&num=%d&lr=lang_en' % (time, num)
        response = self.get_source(search_url)
        retry_count = 0
        while response is None:
            print('Retrying Connection ...', file=sys.stderr)
            retry_count += 1
            if retry_count > retry:
                print('Reached Retry Limit', file=sys.stderr)
                os._exit(-1)
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
        css_identifier_title = "mCBkyc y355M JQe2Ld nDgy9d"
        css_identifier_link = "WlydOe"
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        titles = soup.findAll("div", {"class": css_identifier_title})
        links = soup.findAll("a", {"class": css_identifier_link})
        for title, link in zip(titles, links):
            results.append({'title': title.get_text() ,'link': link['href']})
        return results

    def generate_url(self, date, num=10):
        search_time = self.get_google_search_date(date)
        links = []
        for query in self.queries:
            results = self.google_search(query, time=search_time, num=num)
            for res in results:
                if res['link'] not in results:
                    links.append(res['link'])
        return links

    def get_google_search_date(self, date):
        if date == datetime.date.today():
            return 'qdr:d'
        else:
            return 'cdr%3A1%2Ccd_min%3A{month}%2F{day}%2F{year}%2Ccd_max%3A{month}%2F{day}%2F{year}'.format(
                month=date.month, day=date.day, year=date.year
            )

# Get Current Time (UTC+8)
def cur_time_str():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S')

def send_links(links, date):
    try:
        print('Sending Links to %s:%d' % (service_host, service_port))
        for link in links:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((service_host, service_port))
            print('-', link)
            outstr = date.strftime('%Y-%m-%d') + ' ' + link + '\n'
            sock.sendall(outstr.encode('ascii'))
            sock.close()
    except socket.error as e:
        print(e, file=sys.stderr)
        os._exit(1)

base_date = datetime.date(2019, 1, 1) # (Y, M, D)
target_date = base_date

# Repeat the Job
@schedule.repeat(schedule.every(30).seconds)
def job():
    print(cur_time_str())
    global target_date
    generator = UrlGenerator()
    results = generator.generate_url(target_date, num=20)
    send_links(results, target_date)
    target_date = target_date + datetime.timedelta(days=1)

if __name__ == '__main__':
    # Initial Job
    job()

    # Check pending job before sleep
    while True:
        schedule.run_pending()
        time.sleep(10)