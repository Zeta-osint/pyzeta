import requests
import argparse
import json
import time
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests_futures.sessions import FuturesSession

from platforms import platforms_username, platforms_email, platforms_api

def print_banner():
    print("""
░▀▀█░█▀▀░▀█▀░█▀█░░░█▀█░█▀▀░▀█▀░█▀█░▀█▀
░▄▀░░█▀▀░░█░░█▀█░░░█░█░▀▀█░░█░░█░█░░█░
░▀▀▀░▀▀▀░░▀░░▀░▀░░░▀▀▀░▀▀▀░▀▀▀░▀░▀░░▀░
        """)

def parser_init() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZETA OSINT is simple open source intelligence tool written in Python")
    parser.add_argument('-v', '--version', action='version', version='ZETA-OSINT 1.0')
    parser.add_argument('-u', '--username', help='Input username')
    parser.add_argument('-e', '--email', help='Input email address')
    parser.add_argument('-o', '--output', dest="save_output", metavar='FILE', help='Save results to a file')
    parser.add_argument('-p', '--profile', dest="profile",metavar="NAME" , help="Search related profiles - API key may required!")
    parser.add_argument('-lpp','--list-profile-platforms', action="store_true", dest="list_profile_platforms", help='Display list of supported for profiles platforms')
    parser.add_argument('-l','--list-platforms', action="store_true", dest="list_platforms", help='Display list of platforms')
    return parser


def fetch_status(session, platform, url, headers):
    try:
        response = session.get(url, headers=headers)
        return platform, url, response
    except requests.RequestException as e:
        return platform, url, None, e

def check_username(platforms_username, username):
    results = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    with FuturesSession(executor=ThreadPoolExecutor(max_workers=10)) as session:
        futures = {
            session.get(url.format(username=username), headers=headers): (platform, url)
            for platform, url in platforms_username.items()
        }

        for future in as_completed(futures):
            platform, url = futures[future]
            try:
                response = future.result()
                if response and response.status_code == 200:
                    results[platform] = response.url + " " + "[Status code:" + str(response.status_code) + "]"
                    print(f"[+] {platform}: {response.url} - Status code: {response.status_code}")
                else:
                    results[platform] = None
                    print(f"[-] {platform}: {url.format(username=username)} - Status code: {response.status_code if response else 'Unknown error'}")
            except Exception as e:
                results[platform] = None
                print(f"[-] {platform}: {url.format(username=username)} - Exception: {str(e)}")

            print(f"Checked {platform} -> Status: {results[platform]}\n")

    return results

def check_email(platforms_email, email):
    results = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    with FuturesSession(executor=ThreadPoolExecutor(max_workers=10)) as session:
        futures = {
            session.get(url.format(email=email), headers=headers): platform
            for platform, url in platforms_email.items()
        }

        for future in as_completed(futures):
            platform = futures[future]
            try:
                response = future.result()
                if response and response.status_code == 200:
                    results[platform] = response.url + " " + "[Status code:" + str(response.status_code) + "]"
                    print(f"[+] {platform}: {response.url} - Status code: {response.status_code}")
                else:
                    results[platform] = None
                    print(f"[-] {platform}: {platforms_email[platform].format(email=email)} - Status code: {response.status_code if response else 'Unknown error'}")
            except Exception as e:
                elapsed_time = time.time() - start_time
                total_time += elapsed_time

                results[platform] = None
                print(f"[-] {platform}: {platforms_email[platform].format(email=email)} - Exception: {str(e)}")

            print(f"Checked {platform} -> Status: {results[platform]}\n")

    return results

def github_api_driver(URL, user_input, output_file):
    output_file = "github-" + output_file # add prefix to file name
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    user_input.replace(" ", "+")

    r = requests.get(URL, f"q={user_input}&type=users", headers=headers)
    print(r.url)
    text = r.text
    text_json = json.loads(text) # convert to json object
    page_count = text_json["payload"]["page_count"] # Get page count
    result_count = text_json["payload"]["result_count"] # Get result count
    profile = text_json["payload"]["results"]

    print(f"Page count: {page_count}")
    print(f"Result count: {result_count}")
    output_file = open(output_file, "w") # BUG: close files
    csv_writer = csv.writer(output_file)

    for page in range(1, page_count+1):
        r = requests.get(URL, f"q={user_input}&type=users&p={page}", headers=headers)
        if r.status_code == 429:
            print("Github API rate limited Reached !! ... retrying in 60 seconds")
            page = page - 2
            time.sleep(40)
            print("resuming :)")
        else:
            text_json = json.loads(r.text)
            text_json = text_json["payload"]["results"]
            count = 0

            # Write data in csv file
            # FIXME: use single write function
            for profile in text_json:
                if count == 0: # write headers
                    header = profile.keys()
                    csv_writer.writerow(header)
                    count += 1
                csv_writer.writerow(profile.values())
            time.sleep(2)

def mastodon_api_driver(URL, user_input, output_file):
    output_file = "mastodon-" + output_file
    MASTODON_API = os.environ.get('MASTODON_API')

    if not MASTODON_API:
        print("Error: Mastodon API token not found!\nSee manual for adding token.") # TODO add in help section
        exit()

    print("Mastodon API Token found!")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
                        'Authorization': f'Bearer {MASTODON_API}'}
    parameters = f"q={user_input}&type=accounts"
    user_input = user_input.replace(" ", "+")


    r = requests.get(URL, parameters, headers=headers)
    print(r.url)
    text = r.text
    text_json = json.loads(text) # convert to json object
    profile = text_json["accounts"]

    output_file = open(output_file, "w") # BUG: close files
    csv_writer = csv.writer(output_file)

    r = requests.get(URL, parameters, headers=headers)
    text_json = json.loads(r.text)
    text_json = text_json["accounts"]

    count = 0
    # Write data in csv file
    # FIXME: use single write function
    for profile in text_json:
            if count == 0: # write headers
                    header = profile.keys()
                    csv_writer.writerow(header)
                    count += 1
            csv_writer.writerow(profile.values())


def write_file(results ,output_file): # BUG: close files
        with open(output_file, 'w') as f:
            for platform, result in results.items():
                f.write(f"{platform}: {result}\n")
        print(f"Results saved to {output_file}")

def main():
    print_banner()
    parser = parser_init()
    args = parser.parse_args()

    if (hasattr(args, "profile") and args.profile):
        if  hasattr(args, "save_output") and args.save_output:
            print("Searching profile")
            github_api_driver(platforms_api["Github"], args.profile, args.save_output)
            mastodon_api_driver(platforms_api["Mastodon"], args.profile, args.save_output)
        else:
            print("Error: profile search can only be used with -o")
            exit()
    elif hasattr(args, "list_profile_platforms") and args.list_profile_platforms:
        for platform_name in platforms_api.keys():
            print(platform_name)
    elif hasattr(args, "list_platforms") and args.list_platforms:
        for platform_name in platforms_username.keys():
            print(platform_name)
    elif hasattr(args, "username") and args.username:
        identifier = args.username.strip().lower().replace(" ", "-")
        results = check_username(platforms_username, identifier)
        if hasattr(args, 'save_output') and args.save_output:
            write_file(results ,args.save_output)
    elif hasattr(args, "email") and args.email:
        identifier = args.email.strip().lower()
        results = check_email(platforms_email, identifier)
        if hasattr(args, 'save_output') and args.save_output:
            write_file(results, args.save_output)
    else:
        print("Error: You must provide either a username or an email address.")
        exit()

if __name__ == "__main__":
    main()
