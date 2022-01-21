import argparse
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


def parse_book_title(soup):
    title, *_ = soup.find("h1").text.split("::")
    return title.strip()


def parse_book_cover_url(soup):
    return soup.find("div", class_="bookimage").find("a").find("img")["src"]


def parse_book_comment_texts(soup):
    comments = soup.find_all("div", class_="texts")
    return [comment.find("span", class_="black").text for comment in comments]


def parse_book_download_link(soup):
    download_txt = soup.find(text='скачать txt')
    if not download_txt:
        return
    tag = download_txt.parent
    if tag.name != "a":
        return
    return tag["href"]


def parse_book_genres(soup):
    genres = soup.find("span", class_="d_book").find_all("a")
    return [genre.text for genre in genres]


def parse_book_page(html_page, base_url):
    soup = BeautifulSoup(html_page, "lxml")
    book = {
        "title": parse_book_title(soup),
        "genres": parse_book_genres(soup),
        "cover_url": urljoin(base_url, parse_book_cover_url(soup)),
        "download_url": None,
        "comments": parse_book_comment_texts(soup),
    }
    download_url = parse_book_download_link(soup)
    if download_url:
        book["download_url"] = urljoin(base_url, download_url)
    return book


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
    comments_dir = "comments"

    os.makedirs(books_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(comments_dir, exist_ok=True)

    for book_id in range(args.start_id, args.end_id + 1):
        book_url = f"http://tululu.org/b{book_id}/"

        response = requests.get(book_url)
        response.raise_for_status()

        try:
            check_for_redirect(response)
        except requests.HTTPError:
            continue

        book = parse_book_page(response.text, response.url)

        if not book["download_url"]:
            continue

        download_txt(book["download_url"], f"{book_id}. {book['title']}.txt")
        download_image(book["cover_url"])
        if book["comments"]:
            save_comments(
                f"{book_id}. {book['title']}.txt", book["comments"]
            )


if __name__ == "__main__":
    main()
