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
        "--start_id",
        type=int,
        default=1,
        help="Начиная с какого ID скачивать книги. По умолчанию: 1",
    )
    parser.add_argument(
        "-e",
        "--end_id",
        type=int,
        default=10,
        help="По какой ID скачивать книги. По умолчанию: 10",
    )
    return parser.parse_args()


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(html_page, base_url):
    soup = BeautifulSoup(html_page, "lxml")

    title, author = soup.find("h1").text.split("::")

    genres = soup.find("span", class_="d_book").find_all("a")

    cover_url = soup.find("div", class_="bookimage").find("a").find("img")["src"]

    comments = soup.find_all("div", class_="texts")

    return {
        "title": title.strip(),
        "author": author.strip(),
        "genres": [genre.text for genre in genres],
        "cover_url": urljoin(base_url, cover_url),
        "comments": [comment.find("span", class_="black").text for comment in comments],
    }


def parse_category_page(html_page, base_url):
    book_urls = []

    soup = BeautifulSoup(html_page, "lxml")

    book_cards = soup.find("div", id="content").find_all("table", class_="d_book")
    for book_card in book_cards:
        book_url_row = book_card.find_all("tr")[1]
        book_relative_url = book_url_row.find("a")["href"]
        book_urls.append(
            {
                "url": urljoin(base_url, book_relative_url),
                "id": int(book_relative_url.replace("/", "").replace("b", "")),
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


def save_comments(filename, comment_texts, folder="comments/"):
    save_path = os.path.join(folder, filename)
    with open(save_path, "w") as file:
        file.write("\n\n".join(comment_texts))
    return save_path


def main():
    args = parse_arguments()

    books_dir = "books"
    images_dir = "images"
    book_database_filepath = "books.json"

    book_database = []

    os.makedirs(books_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    for page in range(1, 2):
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
                book_filepath = download_txt(
                    book_download_url, f"{book_id}. {book['title']}.txt"
                )
                cover_filepath = download_image(book["cover_url"])
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
