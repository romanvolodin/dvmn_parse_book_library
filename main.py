import argparse
import json
import os
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Скрипт для скачивания книг с сайта tululu.org",
    )
    parser.add_argument(
        "-s",
        "--start_page",
        type=int,
        default=1,
        help="Начиная с какой страницы скачивать книги. По умолчанию: 1",
    )
    parser.add_argument(
        "-e",
        "--end_page",
        type=int,
        default=702,
        help="По какую страницу скачивать книги (не включительно). По умолчанию: 702",
    )
    parser.add_argument(
        "--dest_folder",
        type=str,
        default=".",
        help="Путь в каталогу с результатами парсинга. По умолчанию: . (текущий каталог)",
    )
    parser.add_argument(
        "--skip_imgs",
        action="store_true",
        help="Пропустить скачивание картинок.",
    )
    parser.add_argument(
        "--skip_txt",
        action="store_true",
        help="Пропустить скачивание книг.",
    )
    parser.add_argument(
        "--json_path",
        type=str,
        default="./book.json",
        help="Путь к JSON-файлу с результатами. По умолчанию: ./book.json",
    )
    return parser.parse_args()


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(html_page, base_url):
    soup = BeautifulSoup(html_page, "lxml")

    title, author = soup.select_one("h1").text.split("::")

    genres = soup.select("span.d_book a")

    cover_url = soup.select_one(".bookimage a img")["src"]

    comments = soup.select(".texts")

    return {
        "title": title.strip(),
        "author": author.strip(),
        "genres": [genre.text for genre in genres],
        "cover_url": urljoin(base_url, cover_url),
        "comments": [comment.select_one(".black").text for comment in comments],
    }


def parse_category_page(html_page, base_url):
    book_urls = []

    soup = BeautifulSoup(html_page, "lxml")

    book_links = soup.select("#content .d_book tr:nth-of-type(2) a")
    for book_link in book_links:
        book_urls.append(
            {
                "url": urljoin(base_url, book_link["href"]),
                "id": int(book_link["href"].replace("/", "").replace("b", "")),
            }
        )

    return book_urls


def download_txt(url, filename, params=None, folder="books/"):
    response = requests.get(url, params)
    response.raise_for_status()
    check_for_redirect(response)

    save_path = os.path.join(folder, sanitize_filename(filename))
    with open(save_path, "w") as file:
        file.write(response.text)
    return save_path


def download_image(url, params=None, folder="images/"):
    response = requests.get(url, params)
    response.raise_for_status()

    parsed_url = urlparse(unquote(url))

    save_path = os.path.join(folder, os.path.basename(parsed_url.path))
    with open(save_path, "wb") as file:
        file.write(response.content)
    return save_path


def main():
    args = parse_arguments()

    books_dir = f"{args.dest_folder}/books"
    images_dir = f"{args.dest_folder}/images"
    book_database_filepath = f"{args.dest_folder}/{args.json_path}"

    book_database = []

    if not args.skip_txt:
        os.makedirs(books_dir, exist_ok=True)
    if not args.skip_imgs:
        os.makedirs(images_dir, exist_ok=True)

    for page in range(args.start_page, args.end_page):
        scifi_books_url = f"http://tululu.org/l55/{page}"
        response = requests.get(scifi_books_url)
        response.raise_for_status()

        try:
            check_for_redirect(response)
        except requests.HTTPError:
            continue

        category_book_urls = parse_category_page(response.text, response.url)

        for category_book in category_book_urls:
            book_url = category_book["url"]
            book_id = category_book["id"]
            book_download_url = f"http://tululu.org/txt.php?id={book_id}/"

            response = requests.get(book_url)
            response.raise_for_status()

            try:
                check_for_redirect(response)
                book = parse_book_page(response.text, response.url)
                if not args.skip_txt:
                    book_filepath = download_txt(
                        book_download_url,
                        f"{book_id}. {book['title']}.txt",
                        folder=books_dir,
                    )
                if not args.skip_imgs:
                    cover_filepath = download_image(
                        book["cover_url"], folder=images_dir
                    )
            except requests.HTTPError:
                continue

            book_database.append(
                {
                    "title": book["title"],
                    "author": book["author"],
                    "img_src": cover_filepath,
                    "book_path": book_filepath,
                    "comments": book["comments"],
                    "genres": book["genres"],
                }
            )

    with open(book_database_filepath, "w") as file:
        json.dump(book_database, file, ensure_ascii=False)


if __name__ == "__main__":
    main()
