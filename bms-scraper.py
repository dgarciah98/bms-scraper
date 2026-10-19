import json, sys, os, argparse
import wget, requests
from bs4 import BeautifulSoup

import gdown
from onedrivedownloader import download as onedrive_download
from mediafiredl import MediafireDL as MF
from mega_downloader  import download_mega_file

baseurl = "https://manbow.nothing.sh/event/"
excluded_hosts = []

if os.path.exists("excluded_hosts.txt"):
    for l in open("excluded_hosts.txt", "r").readlines():
        excluded_hosts.append(l.strip("\n"))

event_entries = []

def scrape_event_page(event_id: str, start_number: int, end_number: int, write_to_file: bool):
    response = requests.get(f"{baseurl}event.cgi?action=URLList&event={event_id}&start={start_number}&end={end_number}")
    soup = BeautifulSoup(response.text, "html.parser")

    for tr in soup.find_all("tr")[1::]:
        row = tr.td
        url = f"{baseurl}{row.a['href']}"
        number = row.a.text

        row = row.next_sibling
        artist = row.a.text

        row = row.next_sibling
        team = row.text

        row = row.next_sibling
        song_name = row.a.text

        row = row.next_sibling.next_sibling
        dlLinks = []
        for link in row.find_all("a"):
            dlLinks.append(link.text)
            
        event_entries.append({
            "url": url,
            "number": number,
            "artist": artist.encode("latin-1").decode("shift-jis"),
            "title": song_name.encode("latin-1").decode("shift-jis"),
            "team": team.encode("latin-1").decode("shift-jis"),
            "dlLinks": dlLinks            
        })

    if write_to_file:
        with open("bms_event.json", "w+", ) as f:            
            json.dump(event_entries, f, indent=3, ensure_ascii=False)
            
    print(f"finished scraping event page, retrieved {len(event_entries)} entries")

def _handle_error(song: dict, links: list, e: Exception):
    print(f"failed url: {song['url']}")
    print(f"error at line {e.__traceback__.tb_lineno} - {e.__traceback__.tb_frame}")
    print(e)
    links.append(song)
            
def download_bms(file: str, dl_path: str):
    if not os.path.exists(dl_path):
        print(f"path does not exist: {dl_path}")
        return

    if not file:
        download_handler(event_entries, dl_path)
    else:        
        try:
            with open(file) as f:
                download_handler(json.load(f), dl_path)
        except Exception as e:
            print(f"error opening file: {file}")
            print(e)

def download_handler(event: list, dl_path: str):
    total_count = len(event)
    print(f"downloading bms files to directory '{dl_path}', {total_count} files total")
    unsupported_links = []
    failed_links = []
    
    for i, song in enumerate(event):
        urls = song["dlLinks"]
        url_count = len(urls)
        for j, url in enumerate(urls):
            i_plus = i+1
            j_plus = j+1
            if "drive.google.com" in url:
                print(f"\n[{i_plus}/{total_count}] DOWNLOADING GOOGLE DRIVE URL [{j_plus}/{url_count}]\n")                        
                try:
                    if not "folders" in url:
                        gdown.download(url, dl_path, resume=True, retries=3, use_cookies=True, cookies_file="cookies.txt")
                    else:
                        gdown.download_folder(url, output=dl_path, resume=True, retries=3, use_cookies=True, cookies_file="cookies.txt")
                except Exception as e:                            
                    _handle_error(song, failed_links, e)
                    continue
                    
            elif "drive.usercontent.google.com" in url:
                print(f"\n[{i_plus}/{total_count}] DOWNLOADING GOOGLE DRIVE RAW URL [{j_plus}/{url_count}]\n")
                print(f"url: {url}")
                try:
                    wget.download(f"{url}&confirm=t", out=dl_path)
                except Exception as e:
                    _handle_error(song, failed_links, e)
                    continue
                    
            elif "1drv.ms" in url:
                print(f"\n[{i_plus}/{total_count}] DOWNLOADING ONEDRIVE URL [{j_plus}/{url_count}]\n")
                print(f"url: {url}")
                if not "download=1" in url:
                    if not "?" in url:                                
                        url = f"{url}?download=1"
                    else:
                        url = f"{url}&download=1"
                try:
                    ret = onedrive_download(url=f"{url}&download=1", filename=dl_path, unzip=False, unzip_path=dl_path)
                    print(ret)
                except Exception as e:
                    _handle_error(song, failed_links, e)
                    continue
                            
            elif "mediafire.com" in url:
                print(f"\n[{i_plus}/{total_count}] DOWNLOADING MEDIAFIRE URL [{j_plus}/{url_count}]\n")
                try:
                    mf_filename = MF.GetName(url)
                    print(mf_filename)
                    if not os.path.exists(f"{dl_path}/{mf_filename}"):                                
                        MF.Download(url, dl_path)
                    else:
                        print("file already downloaded")
                except Exception as e:
                    _handle_error(song, failed_links, e)
                    continue
                    
            elif "dropbox.com" in url:
                print(f"\n[{i_plus}/{total_count}] DOWNLOADING DROPBOX URL [{j_plus}/{url_count}]\n")
                if "dl=0" in url:
                    url = url.replace("dl=0", "dl=1")
                try:
                    gdown.download(url, dl_path, resume=True, retries=3)
                except Exception as e:
                    _handle_error(song, failed_links, e)
                    continue
                        
            elif "mega.nz" in url:
                print(f"\n[{i_plus}/{total_count}] DOWNLOADING MEGA URL [{j_plus}/{url_count}]\n")
                print(f"url: {url}")
                try:
                    download_mega_file(url, dl_path)
                except Exception as e:
                    _handle_error(song, failed_links, e)
                    continue
                
            else:
                print("\nRANDOM URL, CHECKING EXCLUDED HOSTS")
                if any(s in url for s in excluded_hosts):
                    print(f"SKIPPING URL: {url}")
                    unsupported_links.append(song)
                    continue
                else:
                    print(f"URL CAN BE DOWNLOADED: {url}")
                    try:                        
                        gdown.download(url, dl_path, resume=True, retries=3, use_cookies=True)
                    except Exception as e:
                        _handle_error(song, failed_links, e)
                        continue
            print("DOWNLOADED SUCCESSFULLY")
                    
    if unsupported_links:
        print("found unsupported urls, writing to 'unsupported_links.json'")
        try:            
            with open("unsupported_links.json", "w+") as f:
                json.dump(unsupported_links, f, indent=3, ensure_ascii=False)
        except Exception as e:
            print("failed to write unsupported_links.json")
            print(e)

    if failed_links:
        print("found failed urls, writing to 'failed_links.json'")
        res = []
        for d in failed_links:
            if not d in res:
                res.append(d)

        try:
            with open("failed_links.json", "w+") as f:
                json.dump(res, f, indent=3, ensure_ascii=False)
        except Exception as e:
            print("failed to write failed_links.json")
    
if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            description="Manbow Event page BMS downloader",
            usage="%(prog)s [options]",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("-e", "--event", help="Manbow Event ID, for scraping download links")
        parser.add_argument("-f", "--file", help="Path to event entries JSON file")
        parser.add_argument("-o", "--output-path", default="./bms-downloads", help="Where to download files")
        parser.add_argument("-wf", "--dont-write-event-to-file", help="Whether to write or not scraped results to a JSON file", action="store_false")
        parser.add_argument("-d", "--download", help="Download files after scraping webpage", action="store_true")
        parser.add_argument("-sn", "--start-number", type=int, default=0, help="Starting entry number, will download from this entry onwards")
        parser.add_argument("-en", "--end-number", type=int, default=999, help="Ending entry number, will download up to this entry")
        args = parser.parse_args()
        event = args.event
        urls_file = args.file
        path = args.output_path
        write_to_file = args.dont_write_event_to_file
        download = args.download
        start_number = args.start_number
        end_number = args.end_number

        if path and path == "./bms-downloads" and not os.path.exists(path):
            os.makedirs(path)
        
        if args.event:
            print(f"scraping page from event id {event}")
            print(f"scraping from entry number {start_number}")
            print(f"scraping up to entry number {end_number}")
            scrape_event_page(event, start_number, end_number, write_to_file)            
            if download:
                download_bms("", path)
                
        if urls_file:
            download_bms(urls_file, path)
            
    except Exception as e:
        print("something failed")
        print(f"{e} at line {e.__traceback__.tb_lineno} - {e.__traceback__.tb_frame}")

    sys.exit()
