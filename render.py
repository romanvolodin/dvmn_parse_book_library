import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server, shell
from more_itertools import chunked


def on_reload():
    with open("scifi_books/books.json", "r") as file:
        books = json.load(file)

    for book in books:
        book["img_src"] = book["img_src"].replace("scifi_books/", "")

    books = list(chunked(books, 12))
    books1, books2 = books

    env = Environment(
        loader=FileSystemLoader("./templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")
    page = template.render({"books1": books1, "books2": books2})

    with open("scifi_books/index.html", "w") as file:
        file.write(page)


if __name__ == "__main__":
    on_reload()

    server = Server()
    server.watch("templates/*.html", shell("make html", cwd="docs"))
    server.serve(root="scifi_books/")
