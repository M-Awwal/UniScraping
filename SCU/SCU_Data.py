import copy
import csv
import json
import re
import time
from pathlib import Path

# noinspection PyProtectedMember
from urllib.parse import urljoin

from bs4 import Comment
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from CustomMethods import DurationConverter, TemplateData
import bs4 as bs4
import requests
import os

from CustomMethods.DurationConverter import convert_duration


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


def save_data_json(title__, data__):
    with open(title__, 'w', encoding='utf-8') as f:
        json.dump(data__, f, ensure_ascii=False, indent=2)


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title__', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body_):
    soup_ = bs4.BeautifulSoup(body_, 'html.parser')
    texts = soup_.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


def tag_text(tag):
    return tag.get_text().__str__().strip()


def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


# selenium web driver
# we need the Chrome driver to simulate JavaScript functionality
# thus, we set the executable path and driver options arguments
# ENSURE YOU CHANGE THE DIRECTORY AND EXE PATH IF NEEDED (UNLESS YOU'RE NOT USING WINDOWS!)
option = webdriver.ChromeOptions()
option.add_argument(" - incognito")
option.add_argument("headless")
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

delay = 2

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/scu_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'SCU_All_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

course_data_template = {'Level_Code': '', 'University': 'Southern Cross University', 'City': '', 'Course': '',
                        'Faculty': '',
                        'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                        'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                        'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                        'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                        'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
                        'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                        'Career_Outcomes': '',
                        'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No',
                        'Face_to_Face': 'Yes',
                        'Blended': 'No', 'Remarks': '',
                        'Subject_or_Unit_1': '', 'Subject_Objective_1': '', 'Subject_Description_1': '',
                        'Subject_or_Unit_2': '', 'Subject_Objective_2': '', 'Subject_Description_2': '',
                        'Subject_or_Unit_3': '', 'Subject_Objective_3': '', 'Subject_Description_3': '',
                        'Subject_or_Unit_4': '', 'Subject_Objective_4': '', 'Subject_Description_4': '',
                        'Subject_or_Unit_5': '', 'Subject_Objective_5': '', 'Subject_Description_5': '',
                        'Subject_or_Unit_6': '', 'Subject_Objective_6': '', 'Subject_Description_6': '',
                        'Subject_or_Unit_7': '', 'Subject_Objective_7': '', 'Subject_Description_7': '',
                        'Subject_or_Unit_8': '', 'Subject_Objective_8': '', 'Subject_Description_8': '',
                        'Subject_or_Unit_9': '', 'Subject_Objective_9': '', 'Subject_Description_9': '',
                        'Subject_or_Unit_10': '', 'Subject_Objective_10': '', 'Subject_Description_10': '',
                        'Subject_or_Unit_11': '', 'Subject_Objective_11': '', 'Subject_Description_11': '',
                        'Subject_or_Unit_12': '', 'Subject_Objective_12': '', 'Subject_Description_12': '',
                        'Subject_or_Unit_13': '', 'Subject_Objective_13': '', 'Subject_Description_13': '',
                        'Subject_or_Unit_14': '', 'Subject_Objective_14': '', 'Subject_Description_14': '',
                        'Subject_or_Unit_15': '', 'Subject_Objective_15': '', 'Subject_Description_15': '',
                        'Subject_or_Unit_16': '', 'Subject_Objective_16': '', 'Subject_Description_16': '',
                        'Subject_or_Unit_17': '', 'Subject_Objective_17': '', 'Subject_Description_17': '',
                        'Subject_or_Unit_18': '', 'Subject_Objective_18': '', 'Subject_Description_18': '',
                        'Subject_or_Unit_19': '', 'Subject_Objective_19': '', 'Subject_Description_19': '',
                        'Subject_or_Unit_20': '', 'Subject_Objective_20': '', 'Subject_Description_20': '',
                        'Subject_or_Unit_21': '', 'Subject_Objective_21': '', 'Subject_Description_21': '',
                        'Subject_or_Unit_22': '', 'Subject_Objective_22': '', 'Subject_Description_22': '',
                        'Subject_or_Unit_23': '', 'Subject_Objective_23': '', 'Subject_Description_23': '',
                        'Subject_or_Unit_24': '', 'Subject_Objective_24': '', 'Subject_Description_24': '',
                        'Subject_or_Unit_25': '', 'Subject_Objective_25': '', 'Subject_Description_25': '',
                        'Subject_or_Unit_26': '', 'Subject_Objective_26': '', 'Subject_Description_26': '',
                        'Subject_or_Unit_27': '', 'Subject_Objective_27': '', 'Subject_Description_27': '',
                        'Subject_or_Unit_28': '', 'Subject_Objective_28': '', 'Subject_Description_28': '',
                        'Subject_or_Unit_29': '', 'Subject_Objective_29': '', 'Subject_Description_29': '',
                        'Subject_or_Unit_30': '', 'Subject_Objective_30': '', 'Subject_Description_30': '',
                        'Subject_or_Unit_31': '', 'Subject_Objective_31': '', 'Subject_Description_31': '',
                        'Subject_or_Unit_32': '', 'Subject_Objective_32': '', 'Subject_Description_32': '',
                        'Subject_or_Unit_33': '', 'Subject_Objective_33': '', 'Subject_Description_33': '',
                        'Subject_or_Unit_34': '', 'Subject_Objective_34': '', 'Subject_Description_34': '',
                        'Subject_or_Unit_35': '', 'Subject_Objective_35': '', 'Subject_Description_35': '',
                        'Subject_or_Unit_36': '', 'Subject_Objective_36': '', 'Subject_Description_36': '',
                        'Subject_or_Unit_37': '', 'Subject_Objective_37': '', 'Subject_Description_37': '',
                        'Subject_or_Unit_38': '', 'Subject_Objective_38': '', 'Subject_Description_38': '',
                        'Subject_or_Unit_39': '', 'Subject_Objective_39': '', 'Subject_Description_39': '',
                        'Subject_or_Unit_40': '', 'Subject_Objective_40': '', 'Subject_Description_40': ''
                        }

possible_cities = {'gold coast': 'Gold Coast',
                   'lismore': 'New South Wales',
                   'brisbane': 'Brisbane',
                   'melbourne': 'Melbourne',
                   'coomera': 'Gold Coast',
                   'sydney': 'Sydney',
                   'coffs harbour': 'New South Wales',
                   'new south wales': 'New South Wales',
                   'online': ''}

other_cities = {}

campuses = set()

sample = ["https://www.scu.edu.au/study-at-scu/courses/master-of-teaching-1207286/2021/"]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'University of South Australia', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': '',
                   'Subject_or_Unit_1': '', 'Subject_Objective_1': '', 'Subject_Description_1': '',
                   'Subject_or_Unit_2': '', 'Subject_Objective_2': '', 'Subject_Description_2': '',
                   'Subject_or_Unit_3': '', 'Subject_Objective_3': '', 'Subject_Description_3': '',
                   'Subject_or_Unit_4': '', 'Subject_Objective_4': '', 'Subject_Description_4': '',
                   'Subject_or_Unit_5': '', 'Subject_Objective_5': '', 'Subject_Description_5': '',
                   'Subject_or_Unit_6': '', 'Subject_Objective_6': '', 'Subject_Description_6': '',
                   'Subject_or_Unit_7': '', 'Subject_Objective_7': '', 'Subject_Description_7': '',
                   'Subject_or_Unit_8': '', 'Subject_Objective_8': '', 'Subject_Description_8': '',
                   'Subject_or_Unit_9': '', 'Subject_Objective_9': '', 'Subject_Description_9': '',
                   'Subject_or_Unit_10': '', 'Subject_Objective_10': '', 'Subject_Description_10': '',
                   'Subject_or_Unit_11': '', 'Subject_Objective_11': '', 'Subject_Description_11': '',
                   'Subject_or_Unit_12': '', 'Subject_Objective_12': '', 'Subject_Description_12': '',
                   'Subject_or_Unit_13': '', 'Subject_Objective_13': '', 'Subject_Description_13': '',
                   'Subject_or_Unit_14': '', 'Subject_Objective_14': '', 'Subject_Description_14': '',
                   'Subject_or_Unit_15': '', 'Subject_Objective_15': '', 'Subject_Description_15': '',
                   'Subject_or_Unit_16': '', 'Subject_Objective_16': '', 'Subject_Description_16': '',
                   'Subject_or_Unit_17': '', 'Subject_Objective_17': '', 'Subject_Description_17': '',
                   'Subject_or_Unit_18': '', 'Subject_Objective_18': '', 'Subject_Description_18': '',
                   'Subject_or_Unit_19': '', 'Subject_Objective_19': '', 'Subject_Description_19': '',
                   'Subject_or_Unit_20': '', 'Subject_Objective_20': '', 'Subject_Description_20': '',
                   'Subject_or_Unit_21': '', 'Subject_Objective_21': '', 'Subject_Description_21': '',
                   'Subject_or_Unit_22': '', 'Subject_Objective_22': '', 'Subject_Description_22': '',
                   'Subject_or_Unit_23': '', 'Subject_Objective_23': '', 'Subject_Description_23': '',
                   'Subject_or_Unit_24': '', 'Subject_Objective_24': '', 'Subject_Description_24': '',
                   'Subject_or_Unit_25': '', 'Subject_Objective_25': '', 'Subject_Description_25': '',
                   'Subject_or_Unit_26': '', 'Subject_Objective_26': '', 'Subject_Description_26': '',
                   'Subject_or_Unit_27': '', 'Subject_Objective_27': '', 'Subject_Description_27': '',
                   'Subject_or_Unit_28': '', 'Subject_Objective_28': '', 'Subject_Description_28': '',
                   'Subject_or_Unit_29': '', 'Subject_Objective_29': '', 'Subject_Description_29': '',
                   'Subject_or_Unit_30': '', 'Subject_Objective_30': '', 'Subject_Description_30': '',
                   'Subject_or_Unit_31': '', 'Subject_Objective_31': '', 'Subject_Description_31': '',
                   'Subject_or_Unit_32': '', 'Subject_Objective_32': '', 'Subject_Description_32': '',
                   'Subject_or_Unit_33': '', 'Subject_Objective_33': '', 'Subject_Description_33': '',
                   'Subject_or_Unit_34': '', 'Subject_Objective_34': '', 'Subject_Description_34': '',
                   'Subject_or_Unit_35': '', 'Subject_Objective_35': '', 'Subject_Description_35': '',
                   'Subject_or_Unit_36': '', 'Subject_Objective_36': '', 'Subject_Description_36': '',
                   'Subject_or_Unit_37': '', 'Subject_Objective_37': '', 'Subject_Description_37': '',
                   'Subject_or_Unit_38': '', 'Subject_Objective_38': '', 'Subject_Description_38': '',
                   'Subject_or_Unit_39': '', 'Subject_Objective_39': '', 'Subject_Description_39': '',
                   'Subject_or_Unit_40': '', 'Subject_Objective_40': '', 'Subject_Description_40': ''
                   }

    actual_cities = []

    browser.get(each_url)
    time.sleep(1.5)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    h1 = soup.find('h1', {'class': 'pageTitleFixSource'})
    if h1:
        course_data['Course'] = tag_text(h1)

    # CITY
    try:
        div = soup.find('div', {'class': 'table-grid table-col-3 table-responsive no-overflow'})
        if div:
            dom_id = div.find('a', text=re.compile('Domestic snapshot', re.IGNORECASE))
            if dom_id:
                dom_table = div.find_all('table', {'class': 'table'})[0]
                if dom_table:
                    dom_tbody = dom_table.find('tbody')
                    if dom_tbody:
                        tr_tags = dom_tbody.find_all('tr')
                        if tr_tags:
                            for tr in tr_tags:
                                td_tags = tr.find_all('td')
                                if td_tags:
                                    data_list = [tag_text(i) for i in td_tags]
                                    for i in data_list:
                                        for j in possible_cities:
                                            if i.lower() == j.lower() or j.lower() in i.lower():
                                                actual_cities.append(j.lower())
                                                print('city spotted: ', possible_cities[j])
                                            if 'online' in i.lower():
                                                course_data['Online'] = 'Yes'
            else:
                course_data['Availability'] = 'I'
    except (AttributeError, IndexError):
        div = soup.find('div', {'class': 'table-grid table-col-3 table-responsive no-overflow'})
        if div:
            int_id = div.find('a', text=re.compile('International snapshot', re.IGNORECASE))
            if int_id:
                int_table = div.find_all('table', {'class': 'table'})[1]
                if int_table:
                    int_tbody = int_table.find('tbody')
                    if int_tbody:
                        tr_tags = int_tbody.find_all('tr')
                        if tr_tags:
                            for tr in tr_tags:
                                td_tags = tr.find_all('td')
                                if td_tags:
                                    data_list = [tag_text(i) for i in td_tags]
                                    for i in data_list:
                                        for j in possible_cities:
                                            if i.lower() == j.lower() or j.lower() in i.lower():
                                                actual_cities.append(j.lower())
                                                print('city spotted: ', possible_cities[j])
                                            if 'online' in i.lower():
                                                course_data['Online'] = 'Yes'
            else:
                course_data['Availability'] = 'D'

    # AVAILABILITY
    h3 = soup.find('h3', text=re.compile('This course is available to:', re.IGNORECASE))
    if h3:
        main_div = h3.find_parent('div').find_parent('div')
        if main_div:
            all_divs = main_div.find_all('div')
            if all_divs:
                div_text_list = [tag_text(d) for d in all_divs]
                div_text = ' '.join(div_text_list)
                int_student_in_aus = 'international students studying in australia'
                int_student_out_aus = 'international students studying online or outside australia'
                dom_students = 'australian/domestic students'

                if dom_students in div_text.lower() and \
                        int_student_in_aus not in div_text.lower() and \
                        int_student_out_aus not in div_text.lower():
                    course_data['Availability'] = 'D'

                if dom_students not in div_text.lower() and \
                        int_student_in_aus in div_text.lower() or \
                        int_student_out_aus in div_text.lower():
                    course_data['Availability'] = 'I'

                if dom_students in div_text.lower() and \
                        int_student_out_aus in div_text.lower():
                    course_data['Availability'] = 'A'

                if dom_students in div_text.lower() and \
                        int_student_in_aus in div_text.lower():
                    course_data['Availability'] = 'A'

    # DECIDE THE LEVEL CODE
    for i in level_key:
        for j in level_key[i]:
            if j in course_data['Course']:
                course_data['Level_Code'] = i

    # DECIDE THE FACULTY
    for i in faculty_key:
        for j in faculty_key[i]:
            if j.lower() in course_data['Course'].lower():
                course_data['Faculty'] = i
    print('FACULTY: ', course_data['Faculty'])

    # DESCRIPTION
    try:
        THE_XPATH = "//h2[contains(text(), 'Course summary')]/following-sibling::div[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Description'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print(f'cant extract description: {e}')

    # OUTCOMES
    try:
        # noinspection RegExpDuplicateCharacterInClass,SpellCheckingInspection
        p_table = soup.find('div', {'id': 'collapseCrsLO', 'aria-labelledby': 'headingCrsLO'})\
            .find('div', class_='card-body').find('table', class_='table').find('tbody')
        if p_table:
            outcomes = tag_text(p_table)
            course_data['Career_Outcomes'] = outcomes
    except AttributeError:
        print('no outcomes given')

    # REMARKS
    try:
        info_divs = soup.find_all('div', {'class': 'message-box info'})
        if info_divs:
            remarks_list = [tag_text(div) for div in info_divs]
            remarks = '  '.join(remarks_list)
            course_data['Remarks'] = remarks
    except AttributeError:
        print('no remarks')

    # INT FEES
    try:
        table = soup.find('strong', text=re.compile('Annual Fees'))\
            .find_parent('th')\
            .find_parent('tr')\
            .find_parent('thead')\
            .find_parent('table')
        if table:
            fee_tag = table.find('tbody').find('tr').find('td', title='Sessions available for commencing study').find_next('td')
            if fee_tag:
                fee = tag_text(fee_tag).split()[0].replace('$', '')
                course_data['Int_Fees'] = fee
                course_data['Availability'] = 'A'
            else:
                fee_tag = table.find('tbody').find('tr')\
                    .find('td', title='Study Periods available for commencing study')\
                    .find_next('td')
                if fee_tag:
                    fee = tag_text(fee_tag).split()[0].replace('$', '')
                    course_data['Int_Fees'] = fee
                    course_data['Availability'] = 'A'
    except AttributeError:
        try:
            table = soup.find('strong', text=re.compile('Annual Fees')) \
                .find_parent('th') \
                .find_parent('tr') \
                .find_parent('thead') \
                .find_parent('table')
            fee_tag = table.find('tbody').find('tr') \
                .find('td') \
                .find_next('td').find_next('td')
            if fee_tag:
                fee = tag_text(fee_tag).split()[0].replace('$', '')
                course_data['Int_Fees'] = fee
                course_data['Availability'] = 'A'
        except AttributeError:
            print('no fees')

    # DURATION
    try:
        THE_XPATH = "(//td[text()='Duration'][1]/following-sibling::td[1])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text

        duration = convert_duration(value.replace('trimester', 'semester').replace('yrs', 'years'))
        course_data['Duration'] = duration[0]
        course_data['Duration_Time'] = duration[1]
        if duration[0] < 2 and 'month' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Month'
        if duration[0] < 2 and 'year' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Year'
        if 'week' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Weeks'

        if 'full time' in value.lower() or 'full-time' in value.lower():
            course_data['Full_Time'] = 'Yes'
        else:
            course_data['Full_Time'] = 'No'
        if 'part time' in value.lower() or 'part-time' in value.lower():
            course_data['Part_Time'] = 'Yes'
        else:
            course_data['Part_Time'] = 'No'
    except (AttributeError, TypeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract duration')

    # PREREQUISITE 2: IELTS
    try:
        if course_data['Availability'] == 'A':
            td_ielts = soup.find('td', text=re.compile('English language IELTS', re.IGNORECASE))\
                .find_next('td')\
                .find('table')\
                .find('tbody')\
                .find('tr')\
                .find('td', text=re.compile('Overall'))\
                .find_next('td')
            if td_ielts:
                ielts = tag_text(td_ielts)
                course_data['Prerequisite_2'] = 'IELTS'
                course_data['Prerequisite_2_grade_2'] = ielts
    except AttributeError:
        print('No IELTS score')

    # SUBJECTS
    try:
        THE_XPATH = "//tr[@class='unit-row']/td/a[contains(@href, '/study-at-scu/units/')]"
        WebDriverWait(browser, 1).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        values = browser.find_elements_by_xpath(f'{THE_XPATH}')

        a_tags = set().union(i for i in values)
        subjects_links = []
        domain_url = "https://www.scu.edu.au/"
        delay = 3
        for a in a_tags:
            link = a.get_attribute('href')
            if link:
                link_ = urljoin(domain_url, link)
                if link_ not in subjects_links:
                    if link_ not in subjects_links:
                        subjects_links.append(link_)
            if len(subjects_links) is 40:
                break
        i = 1
        for sl in subjects_links:
            browser.get(sl)
            try:
                THE_XPATH = "//h1[1]"
                WebDriverWait(browser, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                value = browser.find_element_by_xpath(f'{THE_XPATH}').text
                course_data[f'Subject_or_Unit_{i}'] = value
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                print(f'cant extract subject name {i}: {e}')
            try:
                THE_XPATH = "//h2[contains(text(), 'Unit description')]/following::*[1]"
                WebDriverWait(browser, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                value = browser.find_element_by_xpath(f'{THE_XPATH}').text
                course_data[f'Subject_Description_{i}'] = value
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                print(f'cant extract subject description {i}: {e}')
            try:
                THE_XPATH = "//h2[contains(text(), 'Unit content')]/following::*[position() < 3]"
                WebDriverWait(browser, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                values = browser.find_elements_by_xpath(f'{THE_XPATH}')
                objectives = str()
                for value in values:
                    objectives += tag_text(bs4.BeautifulSoup('<div>' + value.get_attribute('innerHTML') + '</div>', 'lxml'))
                time.sleep(0.2)
                course_data[f'Subject_Objective_{i}'] = objectives
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                print(f'cant extract subject objective {i}: {e}')
            print(f"SUBJECT {i}: {course_data[f'Subject_or_Unit_{i}']}\n"
                  f"SUBJECT OBJECTIVES {i}: {course_data[f'Subject_Objective_{i}']}\n"
                  f"SUBJECT DESCRIPTION {i}: {course_data[f'Subject_Description_{i}']}\n")
            i += 1
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print(f'cant extract subjects: {e}')

    # duplicating entries with multiple cities for each city
    for i in actual_cities:
        course_data['City'] = possible_cities[i.lower()]
        print('repeated cities: ', course_data['City'])

        if len(course_data['City']) < 2:
            course_data['Face_to_Face'] = 'No'
            course_data['Offline'] = 'No'

        course_data_all.append(copy.deepcopy(course_data))
    del actual_cities

    print('COURSE: ', course_data['Course'])
    print('DESCRIPTION: ', course_data['Description'])
    print('LEVEL CODE: ', course_data['Level_Code'])
    print('CITY: ', course_data['City'])
    print('AVAILABILITY: ', course_data['Availability'])
    print('FACULTY: ', course_data['Faculty'])
    print('INT FEES: ', course_data['Int_Fees'])
    print('LOCAL FEES: ', course_data['Local_Fees'])
    print('ATAR: ', course_data['Prerequisite_1_grade_1'])
    print('IELTS: ', course_data['Prerequisite_2_grade_2'])
    print('GPA: ', course_data['Prerequisite_3_grade_3'])
    print('FULL TIME: ', course_data['Full_Time'])
    print('PART-TIME: ', course_data['Part_Time'])
    print('DISTANCE: ', course_data['Distance'])
    print('BLENDED: ', course_data['Blended'])
    print('OFFLINE: ', course_data['Offline'])
    print('ONLINE: ', course_data['Online'])
    print('FACE TO FACE: ', course_data['Face_to_Face'])
    print('OUTCOMES: ', course_data['Career_Outcomes'])
    print('REMARKS: ', course_data['Remarks'])
    print()

print(*course_data_all, sep='\n')

# tabulate our data__
# course_dict_keys = set().union(*(d.keys() for d in course_data_all))
course_dict_keys = []
for i in course_data_template:
    course_dict_keys.append(i)

with open(csv_file, 'w', encoding='utf-8', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, course_dict_keys)
    dict_writer.writeheader()
    dict_writer.writerows(course_data_all)
