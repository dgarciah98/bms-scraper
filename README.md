# BMS Event Page Scraper
A small Python tool to download all available BMS files from a Manbow event page.

Heavily based on [bofscraper](https://github.com/blobdash/bofscraper) by blobdash.

## How it works
As shown in the help message:
```bash
usage: bms-scraper.py [options]

Manbow Event page BMS downloader

options:
  -h, --help            show this help message and exit
  -e, --event EVENT     Manbow Event ID, for scraping download links (default: None)
  -f, --file FILE       Path to event entries JSON file (default: None)
  -o, --output-path OUTPUT_PATH
                        Where to download files (default: ./bms-downloads)
  -wf, --write-event-to-file
                        Wheter to write scraped results or not to a JSON file (default: True)
  -d, --download        Download files after scraping webpage (default: False)
  -sn, --start-number START_NUMBER
                        Starting entry number, will download from this entry onwards (default: 0)
  -en, --end-number END_NUMBER
                        Ending entry number, will download up to this entry (default: 999)
```

- Provide the event ID from a Manbow event page to retrieve all available download links
- Set `start-number` and/or `end-number` to narrow the selection of available entries
- After retrieving the entries, you can:
  - Download BMS files by providing the resulting JSON file with `-f` flag at a later moment
  - When using `-e` flag, indicate also `-d` flag to automatically download the retrieved entries
  - You can skip generating the JSON file by indicating `-wf` flag
- Download files to a desired path specifing it with `-o` flag, otherwise they will be saved to a default directory

Some links may not work properly and will only download the page itself instead of a ZIP file.

To skip this links, you can create a file called `excluded_hosts.txt` and put the hosts you don't want to download from.
```bash
---excluded_hosts.txt
pan.baidu.com
wwasi.lanzoub.com
wwbfy.lanzn.com
```

When the download process has completed, all entries that have failed downloading or been skipped, will be saved in separated JSON files that can be processed by the tool.

You can fin them in `failed_links.json` and `unsupported_links.json` respectively.

## How to run
For example, run the tool with the following command, having previously installed all dependencies in a `venv`:

```bash
python -m venv ./venv
source venv/bin/activate
pip install -r requirements.txt
python bms-scraper.py -e <event_id> -d -o </your/desired/path>
```

You may also bundle the tool into a executable file. For both Linux and Windows, you may simply run `pyinstaller`:
```bash
pyinstaller -F bms-parser.py
```

If you need to create an EXE file in Linux, you can run [docker-pyinstaller](https://github.com/batonogov/docker-pyinstaller) to build it:
```bash
docker run -v "$(pwd):/src/" --env SPECFILE=bms-scraper.spec batonogov/pyinstaller-windows:latest      
```
