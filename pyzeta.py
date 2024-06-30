import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests_futures.sessions import FuturesSession
import requests
from platforms import platforms_username, platforms_email

class CustomArgumentParser(argparse.ArgumentParser):
    def format_help(self):
        help_msg = super().format_help()
        help_msg = help_msg.replace('optional arguments:', 'Arguments:')
        return help_msg

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

    return results, total_time

def main():
    # Print the banner
    print("#############################################")
    print("#                                           #")
    print("#             ZETA OSINT                    #")
    print("#                                           #")
    print("#############################################")
    print("\n")

    parser = CustomArgumentParser(description="Usage", argument_default=argparse.SUPPRESS)
    parser.add_argument('-v', '--version', action='version', version='ZETA-OSINT 1.0')
    parser.add_argument('-u', '--username', help='Input username')
    parser.add_argument('-e', '--email', help='Input email address')
    parser.add_argument('-o', '--output', dest="save_output", metavar='FILE', help='Save results to a file')
    args = parser.parse_args()

    if hasattr(args, 'username') and args.username:
        identifier = args.username.strip().lower().replace(" ", "-")
        results, total_time = check_username(platforms_username, identifier)
    elif hasattr(args, 'email') and args.email:
        identifier = args.email.strip().lower()
        results, total_time = check_email(platforms_email, identifier)
    else:
        print("Error: You must provide either a username or an email address.")
        return

    print(f"\nEstimated total time: {total_time:.2f} seconds")

    if hasattr(args, 'save_output') and args.save_output:
        with open(args.save_output, 'w') as f:
            for platform, result in results.items():
                f.write(f"{platform}: {result}\n")
        print(f"Results saved to {args.save_output}")

if __name__ == "__main__":
    main()
