import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import sys
import re
from urllib import parse

# Define the following commented-out variables to run this script in your IDE.

# url = "https://your_brightspace_url.com/.../folder_submissions_files.d2l?ou=1&db=2"
# search_for = '''<p>Your (HTML) string here</p>'''
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
):
    parser = argparse.ArgumentParser(
        prog="Brightspace feedback searcher",
        description="This program matches the provided string in submission feedback on Brightspace.",
    )
    parser.add_argument(
        "--submissions_url",
        type=str,
        required=True,
        help='Should have a format similar to "https://your_brightspace_url.com/.../folder_submissions_files.d2l?ou=1&db=2."',
    )
    parser.add_argument(
        "--search_for",
        type=str,
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
    assignment_id = query_def = parse.parse_qs(parse.urlparse(url).query)["db"][0]
    log_file = f"brightspace_feedback_search_results_{course_id}_{assignment_id}_{int(time.time())}.log"

options = webdriver.ChromeOptions()

# Some minor tweaks not to trigger any alarms:
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
options.add_argument("--user-agent=%s" % user_agent)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Prevents printing some irrelevant issues about Chrome
options.add_argument("--log-level=3")

# Prevents Chrome from asking to remember the password
options.add_experimental_option(
    "prefs",
    {"credentials_enable_service": False, "profile.password_manager_enabled": False},
)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)
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
        time.sleep(2)

per_page_select = driver.find_element(By.XPATH, '//select[@name="gridFiles_sl_pgS2"]')
per_page_options = per_page_select.find_elements(By.XPATH, "./option")
if results_per_page not in [10, 20, 50, 100, 200]:
    results_per_page = 200
    starting_page = 1  # To prevent confusions
    print("Invalid value for results_per_page. Using the default values for starting_page and results_per_page...")
    if log_results:
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(f"Invalid value for results_per_page. Using the default values for starting_page and results_per_page...{new_line}")
Select(per_page_select).select_by_value(str(results_per_page))
time.sleep(1)

page_select = driver.find_elements(By.XPATH, '//select[@name="gridFiles_sl_pg2"]')
if len(page_select) > 0:
    if starting_page > 1:
        try:
            Select(page_select[0]).select_by_index(starting_page - 1)
            page_select = driver.find_elements(
                By.XPATH, '//select[@name="gridFiles_sl_pg2"]'
            )
            print(f"Starting with Page {starting_page}")
            if log_results:
                with open(log_file, "w", encoding="UTF-8") as f:
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

with open(log_file, "w", encoding="UTF-8") as f:
    f.write(f"Searched for: {search_for}{new_line}{new_line}Results:{new_line}")
print(f"Searching for: {search_for}")

visited = set()
found = 0
for current_page in range(current_page, total_pages + 1):
    print(f"Page {current_page} of {total_pages}...")

    files = driver.find_elements(By.XPATH, '//span[contains(@class,"dfl")]/a')
    last_checked = 0
    while last_checked < len(files):
        last_checked += 1
        file = driver.find_element(
            By.XPATH, f'(//span[contains(@class,"dfl")]/a)[{last_checked}]'
        )
        onclick_attr = file.get_attribute("onclick")
        onclick_id = (
            onclick_attr.replace("SetReturnPointAndEvaluateFileOrDownload(", "")
            .replace(" );", "")
            .replace("'", "")
            .split(", ")[2]
        )
        if onclick_id not in visited:
            visited.add(onclick_id)
            student = driver.find_element(
                By.XPATH, f'(//td[@class="d_gn d2l-table-cell-last"])[{last_checked}]'
            ).text

            file.click()
            time.sleep(5)

            feedback = driver.execute_script(
                'return document.body.querySelector("d2l-consistent-evaluation").shadowRoot.querySelector("d2l-consistent-evaluation-page").shadowRoot.querySelector("#evaluation-template div:nth-child(3)").querySelector("consistent-evaluation-right-panel").shadowRoot.querySelector("div.d2l-consistent-evaluation-right-panel").querySelector("d2l-consistent-evaluation-right-panel-feedback").shadowRoot.querySelector("d2l-consistent-evaluation-right-panel-block d2l-htmleditor").shadowRoot.querySelector("div.d2l-htmleditor-label-flex-container .d2l-htmleditor-container.d2l-skeletize .d2l-htmleditor-flex-container .d2l-htmleditor-editor-container .tox.tox-tinymce .tox-editor-container .tox-sidebar-wrap .tox-edit-area iframe").contentWindow.document.body.innerHTML'
            )
            if strip_html:
                feedback = re.sub("<[^<]+?>", "", feedback)

            if search_for in feedback:
                found += 1
                student_url = driver.current_url
                if log_results:
                    with open(log_file, "a", encoding="UTF-8") as f:
                        f.write(f"{student}, {student_url}{new_line}")
                print(f"Match found for {student} at {student_url}")
                if pause_when_found:
                    user_input = input(
                        'Enter "exit" (without the quotes) to stop the program. Enter any other input to continue with this search.'
                    )
                    if user_input == "exit":
                        if log_results:
                            with open(log_file, "w", encoding="UTF-8") as f:
                                f.write("Search aborted.")
                        sys.exit(0)
                    print("Searching...")

            driver.execute_script(
                'document.querySelector("d2l-consistent-evaluation").shadowRoot.querySelector("d2l-consistent-evaluation-page").shadowRoot.querySelector("#evaluation-template > div:nth-child(1) > d2l-consistent-evaluation-nav-bar").shadowRoot.querySelector("div > d2l-navigation-immersive > div:nth-child(1) > d2l-navigation-link-back.d2l-full-back").shadowRoot.querySelector("d2l-navigation-link-icon").shadowRoot.querySelector("a").click();'
            )
            time.sleep(1)

    if current_page < total_pages:
        next_page_button = driver.find_element(By.XPATH, '//a[@title="Next Page"]')
        next_page_button.click()
        time.sleep(2)

print(f"{found} matches were found in total.")

if log_results:
    print(f"Search results are saved to {log_file}.")
    with open(log_file, "w", encoding="UTF-8") as f:
        f.write(f"{new_line}{found} matches were found in total.{new_line}")
        f.write(f"Done.{new_line}")

print("Done.")
