import json

from jinja2 import Environment, FileSystemLoader, select_autoescape


if __name__ == "__main__":
    with open("scifi_books/books.json", "r") as file:
        books = json.load(file)

    env = Environment(
        loader=FileSystemLoader("./templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")
    print(template.render({"books": books}))
