import aiohttp
import asyncio
import aiodns
import socket
from aiohttp.resolver import DefaultResolver
from aiofiles import open as aio_open
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import Fore, Back, Style, init
import chardet
import argparse
import ipaddress
import logging
import signal

# Initialize colorama
init(autoreset=True)

# Globals for signal handling and configuration
paused = False
stopped = False
verbose = 0
timeout = 5
search_text = None
case_sensitive = False
proxy = None

class CustomResolver(DefaultResolver):
    def __init__(self, custom_mapping):
        super().__init__()
        self.custom_mapping = custom_mapping

    async def resolve(self, host, port=0, family=socket.AF_INET):
        if host in self.custom_mapping:
            return [{
                'hostname': host,
                'host': self.custom_mapping[host],
                'port': port,
                'family': family,
                'proto': 0,
                'flags': 0,
            }]
        return await super().resolve(host, port, family)

def handle_signal(sig, frame):
    global paused, stopped
    if sig == signal.SIGINT:
        if paused:
            print(f"{Fore.YELLOW}Resuming script...{Style.RESET_ALL}")
            paused = False
        else:
            print(f"{Fore.YELLOW}Pausing script. Press Ctrl+C again to stop.{Style.RESET_ALL}")
            paused = True
    elif sig == signal.SIGTERM:
        print(f"{Fore.RED}Stopping script...{Style.RESET_ALL}")
        stopped = True

async def fetch(session, url, ip, domain, pbar):
    global paused, stopped, verbose, timeout, search_text, case_sensitive

    while paused:
        await asyncio.sleep(0.1)
    if stopped:
        raise asyncio.CancelledError

    headers = {
        'Host': domain,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    logger.debug(f"Sending request to {url} with headers {headers}")

    try:
        async with session.get(url, timeout=timeout, ssl=False, headers=headers, proxy=proxy, allow_redirects=False) as response:
            logger.debug(f"Received response: Status={response.status}, URL={response.url}")

            if response.status == 200:
                await handle_response(response, ip, domain)
            elif response.status in {301, 302}:
                location = response.headers.get('Location')
                logger.debug(f"Redirect found: Location={location}")
                tqdm.write(f"{Fore.YELLOW}Redirect found, real IP for domain {domain} might be: {ip}. Location: {location}{Style.RESET_ALL}")
    except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError,
            aiohttp.ServerTimeoutError, aiohttp.InvalidURL, asyncio.TimeoutError) as e:
        log_error(ip, domain, e)
    except Exception as e:
        log_general_error(ip, domain, e)
    finally:
        pbar.update(1)

async def handle_response(response, ip, domain):
    global search_text, case_sensitive, verbose

    # Read the response content
    content = await response.read()
    detected_encoding = chardet.detect(content)['encoding']
    html = content.decode(detected_encoding, errors='replace')

    # Parse the HTML content
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string.strip() if soup.title else 'No title found'

    logger.debug(f"Response content: {html[:200]}...")  # Log first 200 chars for brevity

    if search_text:
        found = search_text in title if case_sensitive else search_text.lower() in title.lower()
        if found:
            tqdm.write(f"{Fore.BLACK}{Back.GREEN}Real IP for domain {domain} might be: {ip}. Title: {title} (text found){Style.RESET_ALL}")
        else:
            tqdm.write(f"{Fore.GREEN}Real IP for domain {domain} might be: {ip}. Title: {title}{Style.RESET_ALL}")
    else:
        tqdm.write(f"{Fore.GREEN}Real IP for domain {domain} might be: {ip}. Title: {title}{Style.RESET_ALL}")

def log_error(ip, domain, e):
    global verbose

    if isinstance(e, aiohttp.ClientConnectorError):
        if verbose >= 2:
            tqdm.write(f"{Fore.RED}[{ip}] Connection error for {domain}: {e}{Style.RESET_ALL}")
    elif isinstance(e, aiohttp.ClientResponseError):
        if verbose >= 1:
            tqdm.write(f"{Fore.RED}[{ip}] Response error for {domain}: {e.status}, message='{e.message}', url={e.request_info.url}{Style.RESET_ALL}")
    elif isinstance(e, aiohttp.ServerTimeoutError) or isinstance(e, asyncio.TimeoutError):
        if verbose >= 1:
            tqdm.write(f"{Fore.CYAN}[{ip}] Request to {domain} timed out.{Style.RESET_ALL}")
    elif isinstance(e, aiohttp.InvalidURL):
        if verbose >= 1:
            tqdm.write(f"{Fore.RED}[{ip}] Invalid URL for {domain}: {e}{Style.RESET_ALL}")

def log_general_error(ip, domain, e):
    global verbose

    if verbose >= 1:
        tqdm.write(f"{Fore.RED}[{ip}] General error occurred for {domain}: {e}{Style.RESET_ALL}")
        if verbose >= 2:
            tqdm.write(f"{Fore.RED}Traceback: {traceback.format_exc()}{Style.RESET_ALL}")

async def check_domains(domains, ip, pbar):
    custom_resolver = CustomResolver({domain: ip for domain in domains})
    connector = aiohttp.TCPConnector(ssl=False, resolver=custom_resolver)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for domain in domains:
            tasks.append(fetch(session, f"https://{domain}", ip, domain, pbar))
            tasks.append(fetch(session, f"http://{domain}", ip, domain, pbar))
        await asyncio.gather(*tasks)

async def process_ip(ip, domains, semaphore, pbar):
    async with semaphore:
        await check_domains(domains, ip, pbar)

async def parse_ip_list(ip_list_file):
    async with aio_open(ip_list_file, 'r') as f:
        ip_list_raw = await f.readlines()
    ip_list = []
    for line in ip_list_raw:
        line = line.strip()
        if '-' in line:
            start_ip, end_ip = line.split('-')
            ip_list.extend(ip_range(start_ip, end_ip))
        elif '/' in line:
            ip_list.extend(str(ip) for ip in ipaddress.IPv4Network(line))
        else:
            ip_list.append(line)
    return ip_list

def ip_range(start_ip, end_ip):
    start = int(ipaddress.IPv4Address(start_ip))
    end = int(ipaddress.IPv4Address(end_ip))
    return [str(ipaddress.IPv4Address(ip)) for ip in range(start, end + 1)]

async def main(domains, ip_list_file, threads, proxy):
    ip_list = await parse_ip_list(ip_list_file)

    semaphore = asyncio.Semaphore(threads)
    total_tasks = len(ip_list) * len(domains) * 2
    with tqdm(total=total_tasks, desc="Processing IPs and domains") as pbar:
        tasks = [process_ip(ip, domains, semaphore, pbar) for ip in ip_list]
        await asyncio.gather(*tasks)

    print(f"{Fore.GREEN}Finished processing and exiting.{Style.RESET_ALL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check domains against IPs")
    parser.add_argument("domains", help="Comma-separated list of domains")
    parser.add_argument("ip_list_file", help="File containing list of IP addresses")
    parser.add_argument("--verbose", type=int, choices=[0, 1, 2], default=0, help="Set verbosity level (0, 1, or 2)")
    parser.add_argument("--timeout", metavar="seconds", type=int, default=5, help="The timeout for each request in seconds")
    parser.add_argument("--search-text", type=str, help="Text to look for in the title")
    parser.add_argument("--case-sensitive", action="store_true", help="Make text search case sensitive")
    parser.add_argument("--threads", type=int, default=5, help="Number of concurrent threads")
    parser.add_argument("--proxy", type=str, help="Proxy URL (e.g., http://localhost:8080)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    
    # Set logging level based on --debug flag
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logger = logging.getLogger(__name__)
    
    domains = args.domains.split(',')
    ip_list_file = args.ip_list_file
    verbose = args.verbose
    timeout = args.timeout
    search_text = args.search_text
    case_sensitive = args.case_sensitive
    threads = args.threads
    proxy = args.proxy

    signal.signal(signal.SIGINT, handle_signal)

    try:
        asyncio.run(main(domains, ip_list_file, threads, proxy))
    except KeyboardInterrupt:
        print(f"{Fore.RED}Script interrupted.{Style.RESET_ALL}")
