# Model Confrontation (Semantic Debt Analysis)

## 1. The deliberately vague request

```
Write a script to scrape website and save all data, handle the error too
```

## 2. Models tested

| Role            | Model                               |
| --------------- | ----------------------------------- |
| General-purpose | ChatGPT (`GPT-6`)                   |
| Code-oriented   | Claude Opus 5.5 (`claude-opus-5-5`) |

## 3. What each model produced

| Aspect           | ChatGPT (122 lines)                                  | Claude Opus 5.5 (454 lines)                                                                          |
| ---------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Dependencies     | `requests`, `beautifulsoup4` (third-party, unpinned) | Standard library only. The model checked the environment, found `requests` missing, and chose stdlib |
| Scope            | One page                                             | Crawls same-domain links; defaults: 50 pages, depth 2                                                |
| Target           | Hard-coded `https://example.com` (a placeholder domain); the file must be edited to scrape anything else | No default; the URL must be passed on the command line                               |
| What it extracts | `<h2>` titles, their links, timestamp                | Title, meta, headings, visible text, links, images, tables, response headers, raw HTML               |
| Output           | One CSV file                                         | JSON per page, `index.json`, `errors.json`, `scrape.log`, raw HTML files                             |
| Retries          | None                                                 | Exponential backoff; honours `Retry-After` on 429/5xx                                                |
| robots.txt       | Not checked                                          | Checked by default (`--ignore-robots` to disable)                                                    |
| Size limit       | None                                                 | 10 MB per page                                                                                       |
| Duplicate pages  | Not handled                                          | Detected by content hash                                                                             |
| Ctrl+C           | Not handled                                          | Writes partial results before exiting                                                                |
| Tested by the model | No                                                | Yes: `books.toscrape.com` (4 pages), a 404 URL, a DNS failure, an `ftp://` URL                       |

### Test runs

Neither script crawls a real site by default, and the vague request named none, so I chose the test sites myself and gave the same three to both scripts:

1. `https://example.com`: ChatGPT's hard-coded target.
2. `https://books.toscrape.com`: a public sandbox built for scraping practice. Claude had also used it to test its own script.
3. `https://quotes.toscrape.com`: a second sandbox.

ChatGPT's script ran on `example.com` as written. For the other two sites I called its functions directly with the new URL, because its target cannot be changed without editing the file. Claude's script received each URL on the command line, limited to 10 pages and one link deep.

| Site | ChatGPT | Claude |
|---|---|---|
| `example.com` | 0 records. Logged as "Successfully scraped", no CSV written | 1 page saved (the site has only one) |
| `books.toscrape.com` | 0 records, also logged as a success | 10 pages saved (720 KB), 1 duplicate skipped, 63 pages left in the queue |
| `quotes.toscrape.com` | 1 record: `Top Ten tags`, a sidebar heading with no link | 10 pages saved, 2 failed with `HTTP 308 Permanent Redirect` |

- **ChatGPT fails silently.** It only reads `<h2>` tags. Book titles use `<h3>` and `example.com` has no `<h2>`, so it found nothing, yet it reported success and exited normally.
- **Claude saves data that is hard to use.** Prices appear only as loose text lines such as `£45.17`, not linked to a book title, so a second script would be needed to compute anything.
- **Claude's library choice caused a bug.** The author pages on `quotes.toscrape.com` redirect with HTTP 308, which Python 3.9's standard library does not follow. Choosing the standard library to avoid installing anything is what made these pages fail.

## 4. Summary of observed differences

- **Scope.** ChatGPT wrote a one-page extractor for an assumed structure. Claude wrote a multi-page crawler that does not know what the user wants to extract.
- **Target.** ChatGPT invented a target (`example.com`) and a page layout (`<h2>` article titles). Claude left the target to the command line but chose a generic "save everything" design.
- **Error handling.** Both handle errors. Claude's handling is more complete (retries, per-URL error log, parse errors that do not stop the crawl). ChatGPT logs errors but returns an empty list, so a failed run looks like a run with no data.
- **Goal.** Neither script computes what the user actually cares about: the average price per location and price ranges. The vague request did not say so, and neither model asked.
- **Length.** Claude's answer is about four times longer, mostly for features nobody requested.

## 5. Problems and arbitrary choices identified

1. **Invented target and silent failure (ChatGPT).** The script hard-codes `https://example.com` and assumes titles are in `<h2>` tags. In testing, book titles on `books.toscrape.com` use `<h3>` and `example.com` has no headings, so it found 0 records on both. It still logged "Successfully scraped" and exited normally, so an empty result looks like success.
2. **"Save all data" was read two different ways.** ChatGPT saved three fields. Claude saved every page's full text, links, images, tables, and raw HTML. Neither asked which meaning was intended. Claude's reading collects mostly data that is irrelevant to the goal.
3. **Unrequested crawling (Claude).** The request asked for one site's data. Claude added link-following across the domain, with a default of 50 pages. That is a choice the user never made.
4. **Unpinned third-party dependencies (ChatGPT).** It tells the user to `pip install requests beautifulsoup4` without versions and without checking whether they are allowed in this environment.
5. **No security or legal handling in the first answer (both).** Neither response mentioned robots.txt, rate limits, or terms of service at the start. ChatGPT mentions them only at the end, as a note. Claude built in robots.txt checks and a delay, but only because it was not told otherwise.
6. **No clarifying questions (both).** Both went straight to code.

## 6. Self-assessment

Both models made several arbitrary architectural decisions. ChatGPT invented a target site and a page structure, so the code would silently return nothing on any other site. Claude invented a crawl scope, a page limit, and a storage format. Neither model asked which libraries were acceptable: ChatGPT picked unpinned third-party packages, and Claude checked the environment and chose the standard library on its own.

A vague prompt is dangerous in production because the model fills every gap silently. The target, the crawl scope, the request rate, what gets stored, and the failure behaviour are all chosen without anyone deciding them. In practice that can mean crawling a site without permission, sending unbounded load, storing data the business does not need, and producing a pricing average from the wrong fields with no error raised. The failure is quiet, so it is discovered only after the numbers have been used. Neither script was tested against a real property listing site, and neither computes the price averages the user needs, so neither output can be trusted for the actual task yet.
