# FlareHunter

FlareHunter is a robust tool designed to aid in the discovery of the real IP address of websites protected by Cloudflare. Utilizing advanced asynchronous requests and multi-threading capabilities, FlareHunter efficiently checks multiple domains against a list of IP addresses to reveal the actual IP behind the target website. By examining server responses and employing customizable search parameters, FlareHunter aims to uncover the true IP address, bypassing Cloudflare's protection mechanisms.

## Features

- **Multi-threaded Processing**: Define the number of concurrent threads for efficient parallel processing.
- **Asynchronous Requests**: Leveraging `aiohttp` and asyncio for high performance and non-blocking operations.
- **Customizable Search**: Search for specific text within the website title to verify potential IP matches.
- **Error Handling**: Detailed error handling and verbose logging options to monitor and debug the scanning process.
- **Progress Tracking**: Real-time progress bars using `tqdm` to track the overall progress of IP and domain checks.
- **Signal Handling**: Support for pausing and stopping the script gracefully with signal handling.

## Installation

Clone the repository and navigate to the FlareHunter directory:

```bash
git clone https://github.com/yourusername/FlareHunter.git
cd FlareHunter
```
Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run FlareHunter with the desired parameters:

```bash
python flarehunter.py domains ip_list_file
```

* `domains`: Comma-separated list of domains to check.
* `ip_list_file`: File containing the list of IP addresses.
* `--threads`: Number of concurrent threads (default is 5).
* `--verbose`: Set verbosity level (0, 1, or 2).
* `--timeout`: Timeout for each request in seconds (default is 5).
* `--search-text`: Text to look for in the website title.
* `--case-sensitive`: Make the text search case-sensitive.

## Example

```bash
python flarehunter.py example.com,www.example.com ip_list.txt --threads 10 --verbose 2 --timeout 10 --search-text "Welcome" --case-sensitive
```

## Acknowledgements

This project is heavily inspired by [Alaa-abdulridha's CloudSniffer](https://github.com/Alaa-abdulridha/CloudSniffer "Github Repo").

## Disclaimer

This tool is intended for educational and security research purposes only. Use responsibly and **only on domains and IPs that you have permission to test**. The author is not responsible for any misuse or damage caused by this tool.
