from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import shutil
import os
import sys

start_page = 0
images_per_page = 50

base_url = input("Url:")
paggination = input("Number of Pages:")
paggination = int(paggination)

#create directory based on base_url
folder = base_url.replace("https://www.listal.com/", "")
folder = folder.replace("/pictures", "")
if not os.path.exists(folder):
    os.makedirs(folder)

folder = "./"+folder + "/"

def update_progress(progress, total, image):
	filled_length = int(round(100 * progress / float(total)))
	sys.stdout.write('\r [\033[1;34mPROGRESS\033[0;0m] [\033[0;32m{0}\033[0;0m]:{1}% {2}/{3} : {4}'.format('#' * int(filled_length/5), filled_length, progress, total, image))
	if progress == total:sys.stdout.write('\n')
	sys.stdout.flush()

total_image_count = (paggination-start_page) * images_per_page
c = 0
g = 0
print("Total Images:", total_image_count)
x = 0
while x <= paggination:
    if x > 0: url =base_url +"/"+str(x)
    else: url = base_url
    print()
    print("Scrapping from:", url)
        
    try:
        htmldata = urlopen(url,timeout=20)
    except Exception as e:
        print(e)
        continue
    x += 1
    soup = BeautifulSoup(htmldata, 'html.parser')
    images = soup.find_all(class_='imagewrap-inner')
    #Sprint("Found:", len(images), "images")
    y=0
    while y < len(images):
        try:
            #print("Doqnloading image index:", index)
            #print(item.find('a')['href'])
            individual = urlopen(images[y].find('a')['href'], timeout=20)
            individual_soup = BeautifulSoup(individual, 'html.parser')
            found = individual_soup.find(id='itempagewrapper')
            img = (found.find('img')['src'])
            file_name = folder + img.split('/')[-1]

            res = requests.get(img, stream = True)

            if res.status_code == 200:
                exists = os.path.isfile(file_name)
                while exists:
                    #print("file exists:", file_name)
                    g += 1
                    file_name =folder+str(y)+"_"+str(g)+"_"+ img.split('/')[-1]
                    exists = os.path.isfile(file_name)
                
                with open(file_name,'wb') as f:
                    shutil.copyfileobj(res.raw, f) 
                saved = os.path.isfile(file_name)
                if not saved:
                    print(">>>> ",saved)
                    #print('Image sucessfully Downloaded: ',file_name)
                update_progress(c, total_image_count, img.split('/')[-1])
            else:
                print()
                print('Image Couldn\'t be retrieved')
        except Exception as e:
            print(e)
            continue
        y += 1
        c += 1

quit()
