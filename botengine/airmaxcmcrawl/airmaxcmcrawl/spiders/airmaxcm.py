import os
import json
import scrapy
import html2text
from urllib.parse import urljoin
import mysql.connector
# >>> scrapy crawl airmaxcm

class AirmaxcmSpider(scrapy.Spider):
    name = "airmaxcm"
    allowed_domains = ["airmaxcm.com"]
    start_urls = ["https://www.airmaxcm.com/wireless/"]

    def __init__(self, *args, **kwargs):
        super(AirmaxcmSpider, self).__init__(*args, **kwargs)

        if not os.path.exists("output"):
            os.makedirs("output")
        else:
            # Delete Old data 
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            for filename in os.listdir(output_dir):
                file_path = os.path.join(output_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = True
        self.converter.ignore_images = True
        self.converter.ignore_emphasis = True
        self.converter.ignore_tables = True
        self.converter.body_width = 0
        self.urls = []

        self.connection = mysql.connector.connect(
            port=3306,
            user="dbadmin",  
            password="password",  
            database="livehelp_db",
            host="srv590123.hstgr.cloud"
        )

    def parse(self, response):
        text = self.converter.handle(response.body.decode())
        text = text.replace("<|endoftext|>", " ")
        text = text.strip()
        url = response.url.strip("/")
        filename = f"output/{hash(url)}.txt"
        with open(filename, "w", encoding='utf-8') as f:
            f.write(text)

        for link in response.xpath("//a/@href"):
            href = link.get()
            if href.startswith("/wireless/index.php"):
                url = urljoin(response.url, href)
                self.urls.append(url)
                yield scrapy.Request(url, callback=self.parse)
        
        self.update_crawled_urls()

    def update_crawled_urls(self):
        cursor = self.connection.cursor(dictionary=True)
        data_string = json.dumps(self.urls)

        check_query = "SELECT * FROM livehelp_settings WHERE name = %s"
        cursor.execute(check_query, ("crawled_urls",))
        result = cursor.fetchone()
        if result:
            update_query = """
                UPDATE livehelp_settings
                SET value = %s
                WHERE name = %s
            """
            cursor.execute(update_query, (data_string, "crawled_urls"))
        else:
            insert_query = """
                INSERT INTO livehelp_settings (name, value)
                VALUES (%s, %s)
            """
            cursor.execute(insert_query, ("crawled_urls", data_string))
        
        self.connection.commit()
        
        cursor.close()
        self.connection.close()

if __name__ == "__main__":
    AirmaxcmSpider()