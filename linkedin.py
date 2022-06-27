from selenium import webdriver
import time
import requests
import pandas as pd
import html2text
from bs4 import BeautifulSoup

driver = webdriver.Firefox(executable_path="/usr/bin/geckodriver")
alumni = [] # store alumni linkedin profile
data = [] # store alumni data
pre_link = "https://in.linkedin.com/in"

def extract_link(s):
    i = 0; j = 0; n = len(s)
    while s[i] != 'h':
        i += 1
    while (j < n) and (s[j] != '&') and (s[j] != '%'):
        j += 1
    return s[i:j]

for page in range(0,10):
    results = page * 10;
    search = 'site:linkedin.com/in/+AND+"National Institute of Technology, Tiruchirappalli"+AND+"Statistics"+AND+"Computer Science"'
    url = f"https://www.google.com/search?&q={search}&start={results}"
    page = requests.get(url)

    # parse the html page to get all the linkedin_links
    soup = BeautifulSoup(page.text, "html.parser")
    for a_href in soup.find_all("a", href=True):
        if a_href["href"].find("https://in.linkedin.com/in") != -1: #filter out linkedin profiles
            alumni.append(extract_link(a_href["href"]))

# login to linkedin
driver.get('https://www.linkedin.com/login')
driver.find_element_by_id('username').send_keys('rickyalex212@gmail.com')
driver.find_element_by_id('password').send_keys('#Ricky000')
driver.find_element_by_xpath("//*[@type='submit']").click()

for link in alumni:
    try:
        driver.get(link)
        driver.implicitly_wait(1)
        def scroll_down_page(speed=8):
            current_scroll_position, new_height= 0, 1
            while current_scroll_position <= new_height:
                current_scroll_position += speed
                driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
                new_height = driver.execute_script("return document.body.scrollHeight")

        scroll_down_page(speed=8)

        src = driver.page_source
        soup = BeautifulSoup(src, 'lxml')

        # Get Name of the person
        try:
            name_div = soup.find('div', {'class': 'ph5 pb5'})
            first_last_name = name_div.find('h1').get_text().strip()
        except:
            first_last_name = None
        
        # Get profile image url
        try:
            image_tag = name_div.find('img')
            image_url = image_tag['src']
            image_url = image_url.replace("amp;", "")

            # Code to view image via image_url
            """import io
    	    from PIL import Image
    	    
    	    headers=""; timeout=10
    	    with requests.get(image_url, headers=headers, timeout=timeout) as pic:
    	    image_str = pic.content
    	    image_file = io.BytesIO(image_str)
    	    im = Image.open(image_file)
    	    im.show()"""
        except:
            image_url = None
        
        # Get Location of the Person
        try:
            location_tag = soup.find('div', {'class': 'pb2 pv-text-details__left-panel'})
            location = location_tag.find('span').get_text().strip()
        except:
            location = None
        
        # Get Job Title of the Person
        try:
            title_tag = soup.find('div', {'class': 'text-body-medium break-words'})
            title_with_html = str(title_tag)
            h = html2text.HTML2Text()
            title = h.handle(title_with_html).strip()
        except:
            title = None
        
        # Get About the Person
        try:
            about_tag = soup.find('div', {'class': 'display-flex full-width'})
            about = about_tag.find('span').get_text().strip()
            
            if about.find("Endorsed") != -1: # if wrong tag selected
            	about = None
        except:
            about = None
        
        data.append([first_last_name, image_url, title, location, about, link])
        time.sleep(1)

    except:
        continue

column_names = ["Full Name", "Image", "Title", "Location", "About", "Contact"]
df = pd.DataFrame(data, columns=column_names)
df.to_csv('result.csv', index=False)

print(".................Done Scraping!.................	")
driver.quit()
