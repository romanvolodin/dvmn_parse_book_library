import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server, shell
from more_itertools import chunked


def on_reload():
    with open("scifi_books/books.json", "r") as file:
        books = json.load(file)

    for book in books:
        book["img_src"] = book["img_src"].replace("scifi_books/", "")
        book["book_path"] = book["book_path"].replace("scifi_books/", "")

    env = Environment(
        loader=FileSystemLoader("./templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")

    os.makedirs("scifi_books/pages", exist_ok=True)

    for page_number, page_books in enumerate(list(chunked(books, 12)), start=1):
        page = template.render({"books": page_books})
        with open(f"scifi_books/pages/index{page_number}.html", "w") as file:
            file.write(page)


if __name__ == "__main__":
    on_reload()

    server = Server()
    server.watch("templates/*.html", shell("make html", cwd="docs"))
    server.serve(root="scifi_books/")
