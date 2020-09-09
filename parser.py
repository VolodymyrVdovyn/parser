import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
import csv
from lxml import html
import os


def get_company_name(company):
    """Отримуємо повну назву компанії"""
    response = requests.get(f"https://finance.yahoo.com/quote/{company}")
    parsed_page = html.fromstring(response.content)
    company_name = parsed_page.xpath("//h1/text()")[0].split()[0]
    company_name = company_name.split(",")[0]
    return company_name


def cleaning_dict(day, dictionary):
    """Очистка допоміжного словаря від непотрібної інформації"""
    for how_many_days in range(4, 7):
        days_before = str(day - timedelta(how_many_days)).split()[0]
        dictionary.pop(days_before, 0)


def get_current_date():
    """Отримуємо час в секундах з початку епохи для сьогоднішнього дня в 3 години ночі"""
    today = date.today()
    current_date = int(
        datetime(
            year=today.year,
            month=today.month,
            day=today.day,
            hour=3,
            minute=0,
            second=0,
        ).timestamp()
    )
    return current_date


def write_data_in_csv(company_name, data):
    """Оновлюємо данні та записуємо в файл"""
    with open(f"{company_name}_row.csv", "w") as file:
        file.write(data)
    with open(f"{company_name}_row.csv", "r") as csvinput:
        with open(f"{company_name}.csv", "w") as csvoutput:
            writer = csv.writer(csvoutput, lineterminator="\n")
            reader = csv.reader(csvinput)
            all = []
            closing_prise_dict = {}
            row = next(reader)
            row.append("3day_before_change")
            all.append(row)
            for row in reader:
                day = datetime.strptime(row[0], "%Y-%m-%d")
                three_days_before = str(day - timedelta(3)).split()[0]
                cleaning_dict(day, closing_prise_dict)
                if three_days_before in closing_prise_dict:
                    closing_prise = float(row[4])
                    closing_prise_three_days_before = float(
                        closing_prise_dict.pop(three_days_before)
                    )
                    ratio_of_closing_prise = (
                        closing_prise / closing_prise_three_days_before
                    )
                    row.append(ratio_of_closing_prise)
                else:
                    row.append("-")
                closing_prise_dict[row[0]] = row[4]
                all.append(row)
            writer.writerows(all)
    os.remove(f"{company_name}_row.csv")


def get_yahoo_max_data(company):
    current_date = get_current_date()
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{company}?period1=0&period2={current_date}&interval=1d&events=history"
    response = requests.get(url)
    data = response.text
    if response.status_code == 200:
        company_name = get_company_name(company)
        write_data_in_csv(company_name, data)
        print(
            f"Historical prices for the company - {company} are recorded in the file {company_name}.csv"
        )

        get_yahoo_last_news(company, company_name)
    else:
        print(f"Company - {company} not found.")


def get_content(content):
    """Отримуємо останні новини та записуємов список"""
    soup = BeautifulSoup(content, "html.parser")
    items = soup.find_all("li", class_="js-stream-content")
    host = "https://finance.yahoo.com/"

    posts = []
    for item in items:
        posts.append(
            {
                "link": host + item.find("a").get("href"),
                "title": item.find("a").get_text(),
            }
        )
    return posts


def save_news_in_file(items, company_name):
    
    with open(f"{company_name}_news.csv", "w", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(["link", "title"])
        for item in items:
            writer.writerow([item["link"], item["title"]])


def get_yahoo_last_news(company, company_name):
    url = f"https://finance.yahoo.com/quote/{company}"
    response = requests.get(url)
    data = response.text
    posts = get_content(data)
    save_news_in_file(posts, company_name)
    print(
        f"Last news for the company - {company} are recorded in the file {company_name}_news.csv"
    )


if __name__ == "__main__":
    companies = ["PD", "ZUO", "PINS", "ZM", "PVTL", "DOCU", "CLDR", "RUN"]
    for company in companies:
        get_yahoo_max_data(company)
