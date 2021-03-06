"""Description:

    * author: Awwal Mohammed
    * company: Fresh Futures/Seeka Technologies
    * position: IT Intern
    * date: 12-10-20
    * description:This program extracts the corresponding course details and tabulate it.
"""
import csv
import re
import time
from pathlib import Path
from selenium import webdriver
import bs4 as bs4
import requests
import os


def get_page(url):
    """Will download the contents of the page using the requests library.
    :return: a BeautifulSoup object i.e. the content of the webpage related to the given URL.
    """
    # noinspection PyBroadException,PyUnusedLocal
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return bs4.BeautifulSoup(r.content, 'html.parser')
    except Exception as e:
        pass
    return None


def remove_banned_words(to_print, database_regex):
    pattern = re.compile(r"\b(" + "|".join(database_regex) + ")\\W", re.I)
    return pattern.sub("", to_print)


# selenium web driver
# we need the Chrome driver to simulate JavaScript functionality
# thus, we set the executable path and driver options arguments
# ENSURE YOU CHANGE THE DIRECTORY AND EXE PATH IF NEEDED (UNLESS YOU'RE NOT USING WINDOWS!)
option = webdriver.ChromeOptions()
option.add_argument(" - incognito")
option.add_argument("headless")
option.add_argument('--no-sandbox')
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/acu_bachelors_links_file'
course_links_file = open(course_links_file_path, 'r')


# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = csv_file_path.__str__() + 'ACU_bachelors.csv'

bad_words = ['[#435902:0]', 'END', 'START', '#435844', '#', '[', ']', '435902:2', '#435902:3',
             '(pos1) #435848', '[#435902:', '(pos1) #435848', '#435844 [#435902:1]', '#435844',
             '#435844', '[#', '#435844', '#435844', '[#435902:', '#435844', 'START: (pos1) #435862 [#435903:0]',
             'END:  (pos1) #435862', 'START: #435858', 'END:  #435858', 'START: #435858', 'END:  #435858',
             'START: #435858', 'END:  #435858']

course_data = dict()
course_data_all = []
for each_url in course_links_file:
    browser.get(each_url)
    pure_url = each_url.strip()
    each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')
    time.sleep(1)

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE TITLE
    if soup.find('header', class_='col-md-12 desktop-width'):  # check if the course page has a valid title__
        course_title = soup.find('header', class_='col-md-12 desktop-width').text
        course_data['Course'] = course_title.strip().replace('\n', '')
    time.sleep(1)

    # STUDY_MODE
    h3 = soup.find('h3')
    if h3:
        course_data['Study_Mode'] = h3.text

    # AVAILABILITY and LOCATION
    div1 = soup.find('div', class_='box__information--gray box--courses')
    if div1:
        div2 = div1.find('div', class_='col-xs-12 col-sm-6 col-md-6 col-lg-6')
        if div2:
            div3 = div2.find('dl', class_='row')
            if div3:
                dt_all = div3.find_all('dt', class_='col-sm-5 col-md-4')
                dd_all = div3.find_all('dd', class_='col-sm-7 col-md-8')
                dt_items = []
                dd_items = []
                if dt_all and dd_all:
                    for some_dt in dt_all:
                        dt_items.append(some_dt.text)
                    for some_dd in dd_all:
                        dd_items.append(some_dd.text)
                    for key in dt_items:
                        for value in dd_items:
                            course_data[key] = value
                            dd_items.remove(value)
                            break

    # PREREQUISITE_1 (ATAR , and a few other bundled data__)
    div1 = soup.find_all("div", {"class": "col-xs-12 col-sm-6 col-md-6 col-lg-6"})[1]
    if div1:
        dl = div1.find('dl', class_='row')
        if dl:
            dt_all = dl.find_all('dt', class_='col-sm-6 col-md-5')
            dd_all = dl.find_all('dd', class_='col-sm-6 col-md-7')
            if dt_all and dd_all:
                dt_all_text = []
                dd_all_text = []
                for each_dt in dt_all:
                    dt_all_text.append(each_dt.text)
                for each_dd in dd_all:
                    temp_dd_list = []
                    p_dd = each_dd.find('p')
                    if p_dd:
                        temp_dd = []
                        for i in p_dd:
                            if not isinstance(i, bs4.NavigableString):
                                temp_dd.append(i.__str__())
                            elif isinstance(i, bs4.Tag):
                                temp_dd.append(i.name.__str__())
                            else:
                                temp_dd.append(p_dd.get_text())
                        temp_dd = ' '.join(temp_dd)
                        dd_all_text.append(temp_dd)
                    ul_dd = each_dd.find('ul', class_='ret-negated')
                    if ul_dd:
                        li = ul_dd.find_all('li', class_='no_bullet')
                        if li:
                            x1 = [i.text for i in li]
                            x2 = ' '.join(x1)
                            dd_all_text.append(x2)
                for key in dt_all_text:
                    for value in dd_all_text:
                        course_data[key] = value
                        dd_all_text.remove(value)
                        break

    # COURSE START DATE INTERNATIONAL
    if soup('div', {'id': 'course--start-dates--international'}):
        div1 = soup.findAll('div', {'id': 'course--start-dates--international'})[0]
        if div1:
            div2 = div1.find('div', class_='col-md-9')
            if div2:
                all_ul = div2.find_all('ul')
                brisbane_inter_start_date = []
                melbourne_inter_start_date = []
                north_sydney_inter_start_date = []
                all_inter_start_date = []
                if all_ul:
                    for ul in all_ul:
                        li = ul.find('li')
                        if li:
                            li_list = [x.__str__() for x in li]
                            all_inter_start_date.append(' '.join(li_list))

                try:
                    course_data['Brisbane_International_Start_Date'] = \
                        remove_banned_words(all_inter_start_date[0].strip(), bad_words)
                except IndexError:
                    course_data['Brisbane_International_Start_Date'] = 'null'
                try:
                    course_data['Melbourne_International_Start_Date'] = \
                        remove_banned_words(all_inter_start_date[1].strip(), bad_words)
                except IndexError:
                    course_data['Melbourne_International_Start_Date'] = 'null'
                try:
                    course_data['North_Sydney_International_Start_Date'] = \
                        remove_banned_words(all_inter_start_date[2].strip(), bad_words)
                except IndexError:
                    course_data['North_Sydney_International_Start_Date'] = 'null'

    # COURSE DESCRIPTION
    if soup("div", {"id": "course--description--domestic"}):
        div1 = soup.find_all("div", {"id": "course--description--domestic"})[0]
        if div1:
            div2 = div1.find('div', class_='col-md-9 course-info__details')
            if div2:
                all_p = div2.find_all('p')
                if all_p:
                    all_p_list = [i.text for i in all_p]
                    all_p_list_text = ' '.join(all_p_list).strip()
                    course_data['Description'] = all_p_list_text

    # DOMESTIC COURSE PRICE
    div1 = soup.find_all('div', id='course--costs--domestic')
    if div1:
        for div_n in div1:
            div_x = div_n.find('div', class_='col-md-9 course-info__details')
            if div_x:
                ul = div_x.find('ul', class_='list-unstyled')
                if ul:
                    li = ul.find_all('li', class_='no_bullet')
                    if li:
                        dom_costs_list = [' ']
                        for li_p in li:
                            costs_domestic = li_p.contents.__str__().strip()
                            if costs_domestic:
                                costs_domestic = li_p.get_text().strip()
                                dom_costs_list.append(costs_domestic)
                        dom_costs = ' '.join(dom_costs_list)
                        print('DOMESTIC COURSE PRICE: ', dom_costs.strip().replace('\n', '').replace('<', '').replace('>', ''))
                        course_data['Domestic_Course_Price'] = dom_costs.strip()

    # INTERNATIONAL COURSE PRICE
    div1 = soup.find_all('div', id='course--costs--international')
    if div1:
        for div_n in div1:
            div_x = div_n.find('div', class_='col-md-9')
            if div_x:
                ul = div_x.find('ul', class_='no_bullet')
                if ul:
                    li = ul.find_all('li', class_='no_bullet')
                    if li:
                        int_costs_list = [' ']
                        for li_p in li:
                            costs_international = li_p.contents.__str__().strip()
                            if costs_international:
                                costs_international = li_p.get_text().strip()
                                int_costs_list.append(costs_international)
                        int_costs = ' '.join(int_costs_list)
                        print('INTERNATIONAL COURSE PRICE: ', int_costs.strip().replace('\n', '').replace('<', '').replace('>', ''))
                        course_data['International_Course_Cost'] = int_costs.strip()

    course_data = {str(key).strip().replace(':', '').replace('\n', ''): str(item).strip().replace('\n', '') for key, item in course_data.items()}
    course_data_all.append(course_data)

print(*course_data_all, sep='\n')

# tabulate our data__
course_dict_keys = set().union(*(d.keys() for d in course_data_all))

with open(csv_file, 'w', encoding='utf-8', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, course_dict_keys)
    dict_writer.writeheader()
    dict_writer.writerows(course_data_all)
