from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pandas as pd
import re
import locale
import smtplib
locale.setlocale(locale.LC_TIME, "nl_NL") 
    
#%% Set-up

# Credentials ROOM.nl
room_user = ""
room_password = ""

# Credentials Gmail to send mails from
gmail_user = ""
gmail_password = ""

# Destination mail to send mail to
gmail_destination = ""

# Send mail when new room is found
send_mail_new_rooms = True

# Page to scan rooms at
filtered_page = "https://www.room.nl/aanbod/studentenwoningen#?gesorteerd-op=prijs%2B&toekenning=1"

# Set the loop-count, choose this wisely, it determines how many times the script will scroll down to load new rooms, if the number is too low it will not load all rooms
loop_count = 20

# Set the path to chrome
brave_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# %% Set up dataframes

## Make dataframe for personal rooms
try:
    # Check if file exists
    personal_rooms = pd.read_csv('export_dataframe.csv')
        
except:
    # Make dataframe is file doesn't exist
    tmp_columns = ['timestamp','link','rank','total_responses', 'offer_type', 'roommates', 'prijs', 'huurtoeslag']
    personal_rooms = pd.DataFrame(columns = tmp_columns)


# %% Set login function
def login():
    print("Logging in...")
    try:
        
        driver.get(url_login)
        
        time.sleep(2)
        driver.find_element_by_id("username").send_keys(room_user)
        driver.find_element_by_id("password").send_keys(room_password)
        driver.find_element_by_xpath('//*[@id="account-frontend-login"]/login/login-form/div[1]/form/input').click()
        time.sleep(2)
    except:
        pass


#%% Loop
# This variable represents the round
a = 1

while True:
    start_time = datetime.now()
    
    print()
    print()
    print("---------")
    print("Scraping round ", a)
    print("---------")
    print()
    print()
    
    
    ### Webbrowser setup
    ## Used url's to scan for rooms and log in
    url_login = "https://www.room.nl/my-room/inloggen/"
    url_all_rooms = filtered_page
    
    ## Options for the webbrowser
    options = Options()
    options.binary_location = brave_path
    options.add_argument('--headless')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(options=options)

    ### Get the data of personal  
    login()
    
    ## Start the browser and scroll loop_count amount of times through the page to get all the results
    print("Scanning for personal rooms")
    driver.get(url_all_rooms)

    for _ in range(loop_count):
        time.sleep(3)
        driver.find_element_by_tag_name("html").send_keys(Keys.END)
    
    
    ## Get the html data and select the sections with the class list-item
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = soup.find_all('section',class_="list-item")
    
    links_pers = []
    
    ## Extract the data per result (link address in this case)
    for result in results:
        timestamp = datetime.now()
        link = "https://www.room.nl"+result.findChildren('a',href=True)[0]['href']
        properties = result.findChildren('span',class_='object-label-value')
        links_pers.append(link)
    
    print("Scanning ranks...")
    for i in range(len(links_pers)):
        check_if_exists = personal_rooms["link"].str.contains(links_pers[i]).any()
        if(check_if_exists!=True):
            print("Scanning " , i+1 , " of " , len(links_pers))
            driver.get(links_pers[i])
            time.sleep(3)
            driver.find_element_by_tag_name("html").send_keys(Keys.END)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            
            timestamp = datetime.now()
            
            rank = soup.find('div',class_="positie-details").get_text()
            rank = re.findall(r'\d+', rank)
            
            offer_type = driver.find_element_by_xpath('/html/body/div[1]/main/div[1]/div/div/div/div/div[3]/div/div/div[2]/object-labels/ng-include/div/div[1]/span[2]').text;
            
            roommates = driver.find_element_by_xpath('/html/body/div[1]/main/div[1]/div/div/div/div/div[3]/div/div/div[2]/object-labels/ng-include/div/div[4]/span[2]').text;
            
            prijs = driver.find_element_by_xpath('/html/body/div[1]/main/div[1]/div/div/div/div/div[3]/div/div/div[1]/div[1]/div[1]').text;
            
            huurtoeslag = driver.find_element_by_xpath('/html/body/div[1]/main/div[1]/div/div/div/div/div[3]/div/div/div[2]/object-labels/ng-include/div/div[3]/span[2]').text;
            
            try:
                room_data = [timestamp,links_pers[i],rank[0],rank[1], offer_type, roommates, prijs[3:], huurtoeslag]
                
                if(send_mail_new_rooms):
                    # Send mail about newly found room
                    gmail_user = gmail_user
                    gmail_password = gmail_password
                    dest = gmail_destination
                    s = smtplib.SMTP('smtp.gmail.com', 587) 
                    s.starttls() 
                    s.login(gmail_user, gmail_password) 
                    message = "Subject: Nieuwe kamer gevonden \n\nLink: %s \nPrijs:%s \nHuurtoeslag: %s \nOffer type: %s \nRoommates: %s" % (links_pers[i], prijs[3:], huurtoeslag, offer_type, roommates)
                    s.sendmail(gmail_user, dest, message) 
                    s.quit()
                    
                    print("New room found!")                
            
                personal_rooms.loc[len(personal_rooms)] = room_data
            
    
            except:
                pass
            
            # Export data to csv
            personal_rooms.to_csv (r'export_dataframe.csv', index = False, header=True)
        
    driver.quit()
    
    print("----------")
    print("----------")
    print("Scraping round ", a, " done in ", (datetime.now()-start_time))
    print("Pausing for 15 minutes at ", datetime.now())
    print("----------")
    print("----------")

    time.sleep(1000)
    a += 1