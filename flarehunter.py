import aiohttp
import asyncio
import os
import sys
import traceback
import warnings
import argparse
import signal
from aiofiles import open as aio_open
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import Fore, Back, Style, init
import chardet

# Initialize colorama
init(autoreset=True)

# Filter specific warnings
warnings.filterwarnings("ignore", message="It looks like you're parsing an XML document using an HTML parser")

# Globals for signal handling and configuration
paused = False
stopped = False
verbose = 0
timeout = 5
search_text = None
case_sensitive = False

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

    headers = {'Host': domain}

    try:
        async with session.get(url, timeout=timeout, ssl=False, headers=headers) as response:
            if response.status == 200:
                await handle_response(response, ip, domain)
            elif response.status in {301, 302}:
                tqdm.write(f"{Fore.YELLOW}Redirect found, real IP for domain {domain} might be: {ip}{Style.RESET_ALL}")
    except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError,
            aiohttp.ServerTimeoutError, aiohttp.InvalidURL, asyncio.TimeoutError) as e:
        log_error(ip, domain, e)
    except Exception as e:
        log_general_error(ip, domain, e)
    finally:
        pbar.update(1)

async def handle_response(response, ip, domain):
    global search_text, case_sensitive, verbose

    content = await response.read()
    detected_encoding = chardet.detect(content)['encoding']
    html = content.decode(detected_encoding, errors='replace')
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string.strip() if soup.title else 'No title found'

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
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        tasks = []
        for domain in domains:
            tasks.append(fetch(session, f"https://{ip}", ip, domain, pbar))
            tasks.append(fetch(session, f"http://{ip}", ip, domain, pbar))
        await asyncio.gather(*tasks)

async def process_ip(ip, domains, semaphore, pbar):
    async with semaphore:
        await check_domains(domains, ip, pbar)

async def main(domains, ip_list_file, threads):
    async with aio_open(ip_list_file, 'r') as f:
        ip_list = await f.readlines()
    ip_list = [ip.strip() for ip in ip_list]

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

    args = parser.parse_args()
    
    domains = args.domains.split(',')
    ip_list_file = args.ip_list_file
    verbose = args.verbose
    timeout = args.timeout
    search_text = args.search_text
    case_sensitive = args.case_sensitive
    threads = args.threads

    signal.signal(signal.SIGINT, handle_signal)

    try:
        asyncio.run(main(domains, ip_list_file, threads))
    except KeyboardInterrupt:
        print(f"{Fore.RED}Script interrupted.{Style.RESET_ALL}")
