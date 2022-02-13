import argparse
import json
from distutils.dir_util import copy_tree
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Скрипт генерации сайта c книгами для локального просмотра.",
    )
    parser.add_argument(
        "--dest_folder",
        type=str,
        default="scifi_books",
        help="Путь в каталогу с результатами парсинга. По умолчанию: scifi_books",
    )
    parser.add_argument(
        "--json_path",
        type=str,
        default="books.json",
        help="Путь к JSON-файлу с результатами. По умолчанию: scifi_books/books.json",
    )
    parser.add_argument(
        "--livereload",
        action="store_true",
        help="Запустить автоматическую генерацию страниц при обновлении. Удобно при разработке.",
    )
    return parser.parse_args()


def load_template(path, name):
    env = Environment(
        loader=FileSystemLoader(path),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template(name)


def render_webpages(dest_folder="scifi_books", json_path="scifi_books/books.json"):
    with open(json_path, "r") as file:
        books = json.load(file)
    templates_path = "templates"
    template = load_template(templates_path, "index.html")

    books_per_page = 12
    chuncked_books = list(chunked(books, books_per_page))
    for page_number, page_books in enumerate(chuncked_books, start=1):
        page = template.render(
            {
                "books": page_books,
                "page_count": len(chuncked_books),
                "current_page": page_number,
            }
        )
        if page_number == 1:
            page_number = ""
        with open(f"{dest_folder}/index{page_number}.html", "w") as file:
            file.write(page)
    copy_tree(f"{templates_path}/assets", f"{dest_folder}/assets")


if __name__ == "__main__":
    args = parse_arguments()
    json_path = os.path.join(args.dest_folder, args.json_path)
    render_webpages(args.dest_folder, json_path)

    if args.livereload:
        server = Server()
        server.watch("templates/*.html", render_webpages)
        server.serve(root=f"{args.dest_folder}")
