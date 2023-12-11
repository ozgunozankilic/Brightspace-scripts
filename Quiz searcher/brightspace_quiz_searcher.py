import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from webdriver_manager.firefox import GeckoDriverManager
import time
import sys
import re
from urllib import parse
import os

# Define the following commented-out variables to run this script in your IDE.

# url = ""
# search_for = []
# starting_page = 1
# results_per_page = 200
# strip_html = False
# pause_when_found = False
# log_results = True

# If a required parameter is not provided, all parameters are tried to be parsed.
if (
    "url" not in vars()
    or "search_for" not in vars()
    or "starting_page" not in vars()
    or "results_per_page" not in vars()
    or "strip_html" not in vars()
    or "pause_when_found" not in vars()
    or "log_results" not in vars()
    # or "gecko_driver" not in vars()
):
    parser = argparse.ArgumentParser(
        prog="Brightspace quiz searcher",
        description="This program matches the provided string in quizzes on Brightspace.",
    )
    parser.add_argument(
        "--submissions_url",
        type=str,
        required=True,
        help='Should have a format similar to "https://your_brightspace_url.com/.../quiz_mark_attempts.d2l?qi=1&ou=2."',
    )
    parser.add_argument(
        "--search_for",
        type=str,
        metavar="S",
        nargs="*",
        required=True,
        help="A string that will be searched in feedback.",
    )
    parser.add_argument(
        "--starting_page",
        default=1,
        type=int,
        required=False,
        help="The starting page to search for matches.",
    )
    parser.add_argument(
        "--results_per_page",
        default=200,
        type=int,
        required=False,
        help="Must be 10, 20, 50, 100, or 200 (recommended).",
    )
    parser.add_argument(
        "--strip_html",
        default=False,
        required=False,
        const=True,
        action="store_const",
        help="If used, the program will search in clear text instead of HTML.",
    )
    parser.add_argument(
        "--pause_when_found",
        default=False,
        required=False,
        const=True,
        action="store_const",
        help="If used, the program will pause once a match is found before continuing.",
    )
    parser.add_argument(
        "--log_results",
        default=False,
        required=False,
        const=True,
        action="store_const",
        help="If used, the programm will log the results in a file.",
    )

    args = parser.parse_args()
    url = args.submissions_url
    search_for = args.search_for
    starting_page = args.starting_page
    results_per_page = args.results_per_page
    strip_html = args.strip_html
    pause_when_found = args.pause_when_found
    log_results = args.log_results

if log_results:
    new_line = "\n"
    course_id = query_def = parse.parse_qs(parse.urlparse(url).query)["ou"][0]
    quiz_id = query_def = parse.parse_qs(parse.urlparse(url).query)["qi"][0]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(
        current_dir,
        f"brightspace_quiz_search_results_{course_id}_{quiz_id}_{int(time.time())}.log",
    )

opts = Options()
opts.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
)


# Some minor tweaks not to trigger any alarms:
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
opts.add_argument("--user-agent=%s" % user_agent)
opts.add_argument("--disable-blink-features=AutomationControlled")
# opts.add_experimental_option("excludeSwitches", ["enable-automation"])
# opts.add_experimental_option("useAutomationExtension", False)

# Prevents printing some irrelevant issues about Chrome
opts.add_argument("--log-level=3")

driver = webdriver.Firefox(
    service=Service(GeckoDriverManager().install()), options=opts
)

driver.set_window_size(1400, 900)
driver.set_page_load_timeout(45)

driver.get(url)

authenticated = False

print("Waiting for authentication...")
while not authenticated:
    if len(driver.find_elements(By.ID, "formsAuthenticationArea")):
        time.sleep(1)
    else:
        authenticated = True
        print("Authentication successful, redirecting...")
        driver.get(url)
        time.sleep(5)

per_page_select = driver.find_element(
    By.XPATH, '//select[@name="gridAttempts_sl_pgS2"]'
)
per_page_options = per_page_select.find_elements(By.XPATH, "./option")
if results_per_page not in [10, 20, 50, 100, 200]:
    results_per_page = 200
    starting_page = 1  # To prevent confusions
    print(
        "Invalid value for results_per_page. Using the default values for starting_page and results_per_page..."
    )
    if log_results:
        with open(log_file, "a", encoding="UTF-8") as f:
            f.write(
                f"Invalid value for results_per_page. Using the default values for starting_page and results_per_page...{new_line}"
            )
Select(per_page_select).select_by_value(str(results_per_page))
time.sleep(1)

page_select = driver.find_elements(By.XPATH, '//select[@name="gridAttempts_sl_pg2"]')
if len(page_select) > 0:
    if starting_page > 1:
        try:
            Select(page_select[0]).select_by_index(starting_page - 1)
            page_select = driver.find_elements(
                By.XPATH, '//select[@name="gridAttempts_sl_pg2"]'
            )
            print(f"Starting with Page {starting_page}")
            if log_results:
                with open(log_file, "a", encoding="UTF-8") as f:
                    f.write(f"Starting with Page {starting_page}{new_line}")
        except:
            print(
                "Requested page could not be retrieved, starting with the first page..."
            )
    selected_page = Select(page_select[0]).first_selected_option.text.split(" of ")
    current_page = int(selected_page[0])
    total_pages = int(selected_page[1])
else:
    current_page = total_pages = 1

if log_results:
    with open(log_file, "a", encoding="UTF-8") as f:
        f.write(f"Searched for: {search_for}{new_line}{new_line}Results:{new_line}")
print(f"Searching for: {search_for}")

visited = set()
found = 0
for current_page in range(current_page, total_pages + 1):
    print(f"--- Page {current_page} of {total_pages}...")

    quizzes = driver.find_elements(
        By.XPATH,
        '//table[@class="d2l-table d2l-grid d_gl"]//tr//a[@class="d2l-link d2l-link-inline"]',
    )
    for quiz in quizzes:
        quiz_url = quiz.get_attribute("href")

        if quiz_url not in visited:
            driver.execute_script(f'window.open("{quiz_url}", "_blank");')
            driver.switch_to.window(driver.window_handles[1])

            time.sleep(3)

            try:
                student = driver.find_elements(
                    By.XPATH, '//td[@class="d_tl d_tm d_tn"]'
                )[0].text
            except:
                time.sleep(3)
                student = driver.find_elements(
                    By.XPATH, '//td[@class="d_tl d_tm d_tn"]'
                )[0].text
            text = driver.page_source
            if strip_html:
                text = re.sub("<[^<]+?>", "", text)

            is_found = False
            if isinstance(search_for, list):
                for searched in search_for:
                    if searched in text:
                        is_found = True
            else:
                if search_for in text:
                    is_found = True

            if is_found:
                found += 1
                if log_results:
                    with open(log_file, "a", encoding="UTF-8") as f:
                        f.write(f"{student}, {quiz_url}{new_line}")
                print(f"Match found for {student} at {quiz_url}")
                if pause_when_found:
                    user_input = input(
                        'Enter "exit" (without the quotes) to stop the program. Enter any other input to continue with this search: '
                    )
                    if user_input == "exit":
                        if log_results:
                            with open(log_file, "a", encoding="UTF-8") as f:
                                f.write("Search aborted.")
                        sys.exit(0)
                    print("Searching...")

            visited.add(quiz_url)

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)

    if current_page < total_pages:
        Select(
            driver.find_element(By.XPATH, '//*[@name="gridAttempts_sl_pg2"]')
        ).select_by_value(str(current_page + 1))
        time.sleep(5)

print(f"{found} matching attempts were found in total.")

if log_results:
    print(f"Search results are saved to {log_file}.")
    with open(log_file, "a", encoding="UTF-8") as f:
        f.write(f"{new_line}{found} matching attempts were found in total.{new_line}")
        f.write(f"Done.{new_line}")

print("Done.")
