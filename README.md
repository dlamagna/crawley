# Asynchronous web crawler with sleep and filter

This repository contains a customizable web crawler built on top of [Crawl4AI](https://pypi.org/project/crawl4ai). The main goal is to crawl a website, filter out unwanted links, convert pages into Markdown or text, and store the results for further processing or analysis. This is carried out asynchronously and concurrently for efficency, whilst leveraging anti bot detection methods such as a sleep timer and browser selection.

## Key Features

- **Custom filter strategy** to limit crawling to a specific path or subdomain.
- **Concurrent processing** for efficient multi-threaded asynchronous scraping (*not supported*).
- **Sleep timer** between page scrapes for polite crawling or to avoid overloading servers.  
- **Markdown, html, or plain text export** so you can retain links or store raw text.  
- **Automatic folder structure** for storing data and debug logs.

## Folder Structure

Here is an overview of the core files and folders used in this repository:

```
.
├── crawl/                     # Custom functions and classes used in crawling
├── data/                      # Scraped pages saved here
├── debug/                     # Debug logs and URL-to-file mappings
├── crawl_with_sleep.py        # Main crawling script
├── requirements.txt           # Python dependencies
├── setup.sh                   # Setup script for dependencies and tools
└── README.md                  # this file
```


- **crawl/** – Contains utility functions and classes that are used in the main script, including custom BFS crawling strategy.
- **data/** – Where the crawler stores saved pages in the specified format (`.md`/`.txt`/`.html`).
- **debug/** – Contains debug logs, including a JSON file mapping URLs to local filenames.
- **custom_crawl_strategy.py** – Defines `CustomFilteredCrawlStrategy`, extending Crawl4AI’s BFS strategy and limiting crawls to a given base path.
- **crawl_with_sleep.py** – The primary script that handles:
  - Parsing command-line arguments  
  - Initializing and running the crawler  
  - Storing results using the custom strategy  
  - Logging URL-to-filename mappings  
- **requirements.txt** – Python dependencies (including Crawl4AI, BeautifulSoup, Playwright, etc.).
- **setup.sh** – Convenience script to install dependencies, initialize Crawl4AI, and set up Playwright.

## Installation

1. Clone or download this repository (also can be done with SSH):
   ```bash
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo

2. Install dependencies using the setup script. Setting up a virtual enviornment beforehand is advisable.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    sudo chmod +x setup.sh
    ./setup.sh
    ```

3. For manual isntallation (best within a virtual environment): 
    ```bash
    python3 -m pip install -r requirements.txt
    crawl4ai-setup
    crawl4ai-doctor
    playwright install
    sudo chmod 777 debug data
    ```

## Usage

Run the main crawler script, specifying your target URL:

```bash
python crawl_with_sleep.py --url https://www.example.com \
                           --max_depth 2 \
                           --timeout 300000 \
                           --sleep_timer 1.0 \
                           --ext .md
```
Using the default values and shortened argument commands (see next section), a sample command may also be as follows:
```bash 
python crawl_with_sleep.py -u https://www.example.com -d 3
```

### Debug folder

Each crawl will create 2 files within the debug folder:
- JSON mapping: contains a mapping from URL to filename
- Logs: saves all the printed logs to a log file

Both of these files will be named with the scraped URL, depth of the crawl, and the execution time in UTC (+0000).

### Command-Line Arguments

Generally, the parsable arguments have been configured as follows:
- **--url** or **-u**: The base website URL to crawl (required).  
- **--max_depth** or **-d**: Maximum depth to crawl.  
  - Use `-1` for unlimited depth.  
  - `0` for only crawling the base page.  
  - Default is `2`.  
- **--timeout** or **-t**: Timeout (in milliseconds) per page. Defaults to `300000` (5 minutes).  
- **--sleep_timer** or **-s**: Upper bound of randomized sleep timer in seconds after each process completes (default: `2.0`).  
- **--ext**: File extension (`.md`,`.txt`,`.html`) for output. Defaults to `.md`.
- **--concurrent_tasks** or **-c**: Number of concurrent asynchronous tasks for scraping (default: 3).
  * *Concurrent execution is currently not supported byeond the asynchronous nature of Crawl4AI*

***The best way to get the most up to date instructions for a script is with the `-h` function. e.g.***
```
(.venv) dlamagna@LP:~/projects/crawley$ python3 crawl_with_sleep.py -h
usage: crawl_with_sleep.py [-h] -u URL [-d MAX_DEPTH] [-t TIMEOUT] [-s SLEEP_TIMER] [-c CONCURRENT_TASKS] [--ext {.md,.txt,.html}]

Crawl a website using Crawl4AI, convert pages to Markdown, save output immediately, and log URL-to-file mapping.

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     The base website URL to scrape
  -d MAX_DEPTH, --max_depth MAX_DEPTH
                        Maximum depth to crawl (default: 2, use -1 for unlimited, 0 for only the base page).
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout per page request in milliseconds (default: 300000).
  -s SLEEP_TIMER, --sleep_timer SLEEP_TIMER
                        Upper bound of randomized sleep timer in seconds after each process finishes (default: 2.0).
  -c CONCURRENT_TASKS, --concurrent_tasks CONCURRENT_TASKS
                        Number of concurrent asynchronous tasks for scraping (default: 3).
  --ext {.md,.txt,.html}
                        Output file format: .md for Markdown (HTML converted to Markdown) .txt for plain text, .html for raw HTML
```

### Example

```bash
python crawl_with_sleep.py --url https://docs.python.org/3 \
                           --max_depth 1 \
                           --sleep_timer 2.0 \
                           --ext .txt
```

This crawls `docs.python.org/3` up to depth `1`, waits 2 seconds between saving each page, and stores all output as `.txt` files in the `data/` folder.

## Custom Filter Strategy

Inside `custom_crawl_strategy.py`, the `CustomFilteredCrawlStrategy` ensures that only URLs starting with a specified base path are followed. This is useful for avoiding external domains or unrelated sections of a large site.

## Contributing

1. Fork the repository.  
2. Create a new branch (`git checkout -b feature/awesome-feature`).  
3. Commit your changes (`git commit -m 'Add awesome feature'`).  
4. Push to the branch (`git push origin feature/awesome-feature`).  
5. Open a Pull Request.



