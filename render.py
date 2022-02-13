import argparse
import json
import os
from distutils.dir_util import copy_tree

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server, shell
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
        default="scifi_books/books.json",
        help="Путь к JSON-файлу с результатами. По умолчанию: scifi_books/books.json",
    )
    parser.add_argument(
        "--livereload",
        action="store_true",
        help="Запустить автоматическую генерацию страниц при обновлении. Удобно при разработке.",
    )
    return parser.parse_args()


def on_reload(dest_folder, json_path):
    with open(json_path, "r") as file:
        books = json.load(file)

    for book in books:
        book["img_src"] = book["img_src"].replace(f"{dest_folder}/", "")
        book["book_path"] = book["book_path"].replace(f"{dest_folder}/", "")

    env = Environment(
        loader=FileSystemLoader("./templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")

    os.makedirs(f"{dest_folder}/pages", exist_ok=True)
    chuncked_books = list(chunked(books, 12))
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
        with open(f"{dest_folder}/pages/index{page_number}.html", "w") as file:
            file.write(page)
    copy_tree("templates/assets", f"{dest_folder}/pages/assets")


if __name__ == "__main__":
    args = parse_arguments()
    on_reload(args.dest_folder, args.json_path)

    if args.livereload:
        server = Server()
        server.watch("templates/*.html", shell("make html", cwd="docs"))
        server.serve(root=f"{args.dest_folder}/")
