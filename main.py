import os

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def parse_book_title(html_page):
    soup = BeautifulSoup(html_page, "lxml")
    title, *_ = soup.find("h1").text.split("::")
    return title.strip()


def download_txt(url, filename, params=None, folder='books/'):
    response = requests.get(url, params)
    response.raise_for_status()
    try:
        check_for_redirect(response)
        save_path = "{}.txt".format(
            os.path.join(folder, sanitize_filename(filename))
        )
        with open(save_path, "w") as file:
            file.write(response.text)
        return save_path
    except requests.HTTPError:
        pass


def main():
    books_dir = "books"

    os.makedirs(books_dir, exist_ok=True)

    for book_id in range(1, 11):
        book_url = f"http://tululu.org/b{book_id}/"
        book_text_url = f"https://tululu.org/txt.php?id={book_id}"

        response = requests.get(book_url)
        response.raise_for_status()
        title = parse_book_title(response.text)
        download_txt(book_text_url, f"{book_id}. {title}")


if __name__ == "__main__":
    main()
