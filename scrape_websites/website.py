import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
from typing import Optional
from bs4 import BeautifulSoup

def loadEnv() -> str:
    load_dotenv()
    SERP_API_KEY = os.getenv("SERP_API_KEY")

    if not SERP_API_KEY:
        raise ValueError("SERP_API_KEY is missing! Please check your .env file.")
    
    return SERP_API_KEY

SERP_API_KEY = loadEnv()

def get_search_results(query: str) -> list[dict]:

    try:
        headers = {
            "X-API-KEY": SERP_API_KEY,  
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": 10
        }

        response = requests.post("https://google.serper.dev/search", json=payload, headers=headers)
        response.raise_for_status() 

        results = response.json()
        return results.get("organic", [])  
    except Exception as e:
        print(f"\nError fetching search results: {e}\n")
        return []
def generate_website_query(consignee_name: str, location: str) -> str:
    return f'{consignee_name} official website OR homepage OR "about us" OR "about.me" OR "contact us" OR "contact" {location}'

def get_official_website(consignee_name: str, location: str) -> Optional[str]:
    website_url = None
    consignee_terms = consignee_name.lower().split()
    location_terms = location.lower().split()

   
    search_results = get_search_results(generate_website_query(consignee_name, location))

    
    skip_domains = {
        "volza.com", "eximpedia.app", "tradeatlas.com", "trademo.com", "atom.com", "bestfoodimporters.com", "cfaa.cn", "interepo.com", "panjiva.com", "dnb.com", "aduna.com", "tradeint.com", "rocketreach.co", "circlehinternational.org", "ceginformacio.hu", "atninfo.com", "happydog-petfood.com", "disaronno.com", "finalscout.com", "jobcenter.mv", "en.nbd.ltd", "signalhire.com", "producemarketguide.com", "qataroilandgasdirectory.com", "tradeindata.com", "community.upwork.com", "wheree.com", "importgenius.com", "salezshark.com", "sourcing.freshdi.com", "tradedata.pro", "zoominfo.com","perthcafes.com.au"
    }

    
    scored_results = []
    for result in search_results[:5]:  
        score = 0
        link = result.get("link", "").lower()
        parsed_url = urlparse(link)
        domain = parsed_url.netloc
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()

        
        if any(domain.endswith(nd) for nd in skip_domains):
            print(f" Skipping {domain} (Unwanted domain)")
            continue  

        print(f"\n Evaluating: {link}")
        print(f" Initial Score: {score}")

        # company name in domain
        clean_domain = domain.replace("www.", "")
        if consignee_name.lower().replace(" ", "") in clean_domain:
            score += 15  
            print(f"+15 (Company name in domain) | New Score: {score}")

        #  terms from consignee name appear in domain
        if all(term in clean_domain for term in consignee_terms):
            score += 12  
            print(f"+12 (All terms from consignee in domain) | New Score: {score}")

        # company name in title
        if consignee_name.lower() in title:
            score += 8
            print(f"+8 (Company name in title) | New Score: {score}")

        # terms in title
        if all(term in title for term in consignee_terms):
            score += 6
            print(f"+6 (All terms from consignee in title) | New Score: {score}")

        
        location_bonus = 10
        try:
            response = requests.get(link, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = " ".join(soup.stripped_strings).lower() 
                if any(loc in page_text for loc in location_terms):
                    score += location_bonus
                    print(f"{location_bonus} (Location found in webpage content) | New Score: {score}")
                else:
                    score -= 10  
                    print(f"-10 (Location not found in webpage) | New Score: {score}")
        except requests.RequestException as e:
            print(f"Error fetching webpage: {e}")

        #official indicators in title or snippet
        official_indicators = ["official", "homepage", "about us", "contact", "home", "welcome to"]
        if any(indicator in title for indicator in official_indicators):
            score += 5
            print(f"+5 (Official indicator in title) | New Score: {score}")
        if any(indicator in snippet for indicator in official_indicators):
            score += 4
            print(f"+4 (Official indicator in snippet) | New Score: {score}")

       
        non_official_domains = {
            "facebook.com", "linkedin.com", "twitter.com", "instagram.com", 
            "youtube.com", "crunchbase.com", "bloomberg.com", "yelp.com",
            "indeed.com", "glassdoor.com", "bbb.org", "wikipedia.org"
        }
        if any(domain.endswith(nd) for nd in non_official_domains):
            score -= 20  
            print(f"-20 (Non-official domain detected: {domain}) | New Score: {score}")

        #common official TLDs
        official_tlds = {".com", ".org", ".net", ".co", ".com.au",".php",".uk"}
        if any(domain.endswith(tld) for tld in official_tlds):
            score += 3
            print(f"+3 (Official TLD detected) | New Score: {score}")

        official_subpages = {"about-us", "contact", "contact.php", "contactus", "home", "official"}
        subdirs = parsed_url.path.strip("/").split('/')  

        
        if len(subdirs) > 2 and not any(sub in subdirs for sub in official_subpages):
            penalty = min(5, len(subdirs))
            score -= penalty  
            print(f"-{penalty} (Too many subdirectories) | New Score: {score}")

        
        scored_results.append({'score': score, 'link': link, 'domain': domain, 'title': title})

    scored_results.sort(reverse=True, key=lambda x: x['score'])

 
    print(f"\n Final Scores for: {consignee_name}")
    print(f"{'='*60}")
    for idx, result in enumerate(scored_results[:5]):
        print(f"{idx + 1}. Score: {result['score']}, Domain: {result['domain']}")
        print(f"   Title: {result['title']}")
        print(f"   URL: {result['link']}\n")

    
    
    if scored_results:
        website_url = scored_results[0]['link']
    else:
        print(f"No suitable website found for {consignee_name}\n")

    return website_url

# Test Function
# get_official_website("ROYAL DOHA TRADING CONTRACTING AND SERVICES WLL", "Doha")
