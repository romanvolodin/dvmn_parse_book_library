# Парсим онлайн библиотеку

Скрипт скачивает книги с сайта [tululu.org](https://tululu.org/). Для каждой книги дополнительно скачиваются обложка и комментарии.


## Требования

Для запуска вам понадобится Python 3.6 или выше.

## Подготовка

Скачайте код с GitHub. Установите зависимости:

```sh
pip install -r requirements.txt
```

### Запустите скрипт:
```sh
python main.py --start_id=100 --end_id=120
```
Можно не указывать параметры `--start_id` и `--end_id`, по умолчанию будут скачиваться книги, ID которых с 1 по 10.

## Цели проекта

Код написан в учебных целях — для курса по Python на сайте [Devman](https://dvmn.org).