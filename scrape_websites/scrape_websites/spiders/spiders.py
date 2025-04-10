import scrapy
import re
import csv
import os

class ScrapySpider(scrapy.Spider):
    name = "ScrapyVillan"

    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113 Safari/537.36',
        'RETRY_TIMES': 2,
        'REDIRECT_MAX_TIMES': 5,
    }

    def __init__(self, *args, **kwargs):
        super(ScrapySpider, self).__init__(*args, **kwargs)
        self.output_file = 'Contacts_Output.csv'

        if not os.path.exists(self.output_file):
                with open(self.output_file, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['URL', 'Phones', 'Emails'])
    def start_requests(self):
         with open('Only_Websites.csv', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row['Company Website'].strip()
                if url:
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        errback=self.handle_error,
                        dont_filter=True
                    )

    def parse(self, response, **kwargs):
        html = response.text        
        phone_candidates = re.findall(
            r'(?:(?:\+|00)\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}', html
        )
        # rejecting decimal numbers.
        phones = [
        phone.strip() for phone in phone_candidates
        if '.' not in phone and 9 <= len(re.sub(r'\D', '', phone)) <= 15
    ]
        phones = list(dict.fromkeys(phones))
        
        image_exts = ('.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.ico', '.bmp')

        def is_false_positive(email):
            username, domain = email.split('@')
            
            # 1. Exclude image or asset names
            if domain.endswith(image_exts) or any(email.endswith(ext) for ext in image_exts):
                return True

            # 2. Exclude dimensions or version artifacts
            if re.search(r'@\d+x', email):
                return True

            # 3. Exclude UUIDs or hashes as usernames
            if re.fullmatch(r'[a-f0-9\-]{32,}', username):
                return True

            # 4. Domain sanity check
            if not re.search(r'\.[a-z]{2,10}$', domain):
                return True

            return False

        mailto_emails = response.css('a[href^="mailto:"]::attr(href)').getall()
        mailto_emails = [
            e.replace('mailto:', '').split('?')[0] for e in mailto_emails if '@' in e
        ]

        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,63}'
        emails = re.findall(email_pattern, html)

        regex_emails = list(dict.fromkeys(emails))

        emails_r = [
            '{}@{}'.format(*el)
            for el in re.findall('var username = &quot;(.*?)&quot;; var hostname = &quot;(.*?)&quot;',response.text)]
        
        def is_versioned_domain(email):
            domain = email.split('@')[-1]
            parts = domain.split('.')
            num_parts = [p for p in parts if p.isdigit()]
            return len(num_parts) > 1 


        combined = mailto_emails + regex_emails + emails_r
        emails = []
        seen = set()

        for email in combined:
            if email not in seen and not is_versioned_domain(email) and not is_false_positive(email):
                emails.append(email)
                seen.add(email)

        final_phones = ", ".join(phones) if phones else "None"
        final_emails = ", ".join(emails) if emails else "None"

        self.logger.info(f"[{response.url}] Phones: {phones or 'None'}")
        self.logger.info(f"[{response.url}] Emails: {emails or 'None'}")

        yield {
            'url': response.url,
            'phones': phones if phones else None,
            'emails': emails if emails else None
        }

        with open(self.output_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                response.url,
                final_phones,
                final_emails
            ])

    def handle_error(self, failure):
        url = failure.request.url
        self.logger.warning(f"[{url}] Failed to retrieve")
        with open(self.output_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([url, 'None', 'None'])