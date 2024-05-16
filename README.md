# 🐍 FlareHunter

FlareHunter is a robust tool designed to aid in the discovery of the real IP address of websites protected by Cloudflare. Utilizing advanced asynchronous requests and multi-threading capabilities, FlareHunter efficiently checks multiple domains against a list of IP addresses to reveal the actual IP behind the target website. By examining server responses and employing customizable search parameters, FlareHunter aims to uncover the true IP address, bypassing Cloudflare's protection mechanisms.

FlareHunter doesn't modify the systems `hosts` file, so it can test multiple IP addresses at the same time.

[![License](https://img.shields.io/github/license/steffenkloster/FlareHunter)](https://github.com/steffenkloster/FlareHunter/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/steffenkloster/FlareHunter)](https://github.com/steffenkloster/FlareHunter/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/steffenkloster/FlareHunter)](https://github.com/steffenkloster/FlareHunter/network/members)
[![GitHub issues](https://img.shields.io/github/issues/steffenkloster/FlareHunter)](https://github.com/steffenkloster/FlareHunter/issues)

## Features

- **Multi-threaded Processing**: Define the number of concurrent threads for efficient parallel processing.
- **Asynchronous Requests**: Leveraging `aiohttp` and asyncio for high performance and non-blocking operations.
- **Customizable Search**: Search for specific text within the website title to verify potential IP matches.
- **Error Handling**: Detailed error handling and verbose logging options to monitor and debug the scanning process.
- **Progress Tracking**: Real-time progress bars using `tqdm` to track the overall progress of IP and domain checks.
- **Signal Handling**: Support for pausing and stopping the script gracefully with signal handling.

## Requirements

You need Python >= 3.6 to run FlareHunter.

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

**⚠️ Use FlareHunter only on domains and IP addresses for which you have explicit permission to perform testing.**

FlareHunter is intended for educational and security research purposes only. It is designed to help security professionals, researchers, and developers understand the implications of Cloudflare's protection mechanisms and identify potential vulnerabilities in a controlled and authorized environment.

**Important:**

- **Authorization**: Ensure that you have explicit permission from the target website owner before using FlareHunter to discover real IP addresses. Unauthorized use of this tool on websites without permission is illegal and unethical.
- **Responsibility**: The developers and maintainers of FlareHunter are not responsible for any misuse or illegal activity conducted with this tool. Users are solely responsible for their actions and must comply with all applicable laws and regulations.
- **Ethical Use**: Use FlareHunter responsibly and ethically. The primary goal of this tool is to promote better security practices by identifying weaknesses and helping to fortify defenses against potential threats.
- **No Warranty**: FlareHunter is provided "as is" without any warranty of any kind, either expressed or implied. The developers and maintainers do not guarantee that the tool will be effective in all scenarios or that it will not cause unintended consequences.

By using FlareHunter, you agree to adhere to this disclaimer and use the tool in a responsible, ethical, and legal manner.
