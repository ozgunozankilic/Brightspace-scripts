# Feedback searcher

This script can search all student feedback for a specific assignment. It can work in the background without bothering you, and you can read its output or log file later. Alternatively, it can wait for your command each time it finds a match if you intend to make changes to the feedback.

## Requirements

You need [Selenium](https://pypi.org/project/selenium/) and [Webdriver Manager](https://pypi.org/project/webdriver-manager/) packages to run this Python script.

## Usage

The script takes the following arguments:
*   submissions_url: The submission files URL. It should be something like https://your_brightspace_url.com/d2l/lms/dropbox/admin/mark/folder_submissions_files.d2l?ou=1&db=2.
*   search_for: Search string (HTML or clear-text).
*   starting_page: The page from which you want the script to start working. *Optional. Default: 1*
*   results_per_page: Must be 10, 20, 50, 100, or 200 (200 is recommended unless you are not starting from the first page). *Optional. Default: 200*
*   strip_html: A flag that strips the HTML tags from the feedback before the search. *Optional. Default: False*
*   pause_when_found: A flag that makes the script pause whenever it finds a match and inform you. This is useful when you want to change something in every matched feedback. Once it pauses, you need to enter any key in the command line to continue the search (it will prompt you to do so). Entering "exit" (without the quotes) ends the execution. *Optional. Default: False*
*   log_results: A flag that makes the script write the messages and results into a log file in the same directory. *Optional. Default: False*

You can run this script from the command line like this:

```bash
python brightspace_feedback_searcher.py --submissions_url "https://your_brightspace_url.com/d2l/lms/dropbox/admin/mark/folder_submissions_files.d2l?ou=1&db=2" --search_for "Your search string here" --starting_page 2 --results_per_page 200 --strip_html --pause_when_found --log_results
```

This command makes the script browse 200 results per page and starts from the second page. It strips HTML tags, pauses when it finds a match, and logs the results in the same directory.

Once the script is run, it waits for you to log in first, then handles the search by itself. 

## Future improvements

*   It may throw an error if a page takes too long to load, so you might want to change the sleep times. These may be optimized in the future using explicit waits for specific elements to be loaded.
*   A log file name parameter may be added to allow users to specify the log file name and directory. Currently, it uses the course ID, assignment ID, and timestamp to generate the file name.
*   When pausing is activated, it might be a good idea to have the option to force the browser to steal focus to attract the user's attention. 
*   It currently uses the files tab (*folder_submissions_files.d2l*), but making it work with the users tab (*folder_submissions_users.d2l*) may be better.