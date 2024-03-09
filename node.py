import requests
import json
import pandas as pd
import time

# Define the options for retrieving terms
term_options = {
  'url': 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/classSearch/getTerms',
  'params': {
    'searchTerm': '',
    'offset': 1,
    'max': 10 # Change max if needed
  },
  'json': True
}

# Define the options for retrieving subjects
subject_search_options = {
  'url': 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/classSearch/get_subject',
  'params': {
    'term': None,
    'offset': 1,
    'max': 200, # Change max if needed,
    'searchTerm': ''
  },
  'json': True
}

# Define the options for POSTing to search for a term
post_options = {
  'url': 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/term/search',
  'params': {
    'mode': 'search'
  },
  'data': {
    'term': None,
    'studyPath': '',
    'studyPathText': '',
    'startDatepicker': '',
    'endDatepicker': ''
  },
  'cookies': None
}

# Define the options for searching for courses
search_options = {
  'url': 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/searchResults/searchResults',
  'params': {
    'txt_subject': '',
    'txt_courseNumber': '',
    'txt_term': None,
    'startDatepicker': '',
    'endDatepicker': '',
    'pageOffset': '',
    'pageMaxSize': '200',
    'sortColumn': '',
    'sortDirection': ''
  },
  'cookies': None,
  'json': True
}

# Define the options for getting course description
course_description_options = {
  'url': 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/searchResults/getCourseDescription',
  'params': {
    'term': None,
    'courseReferenceNumber': ''
  },
  'cookies': None
}

# Resets the input from last search, so that you can search for a different subject and course number. 
reset_form_options = {
  'url': 'https://nubanner.neu.edu/StudentRegistrationSsb/ssb/classSearch/resetDataForm',
  'cookies': None
}

# Send the request to retrieve terms
term_response = requests.get(**term_options)

# Check if the request was successful
if term_response.status_code == 200:
    upcoming_terms = term_response.json()
    # Setting cookies:
    post_options['cookies'] = term_response.cookies
    search_options['cookies'] = term_response.cookies
    reset_form_options['cookies'] = term_response.cookies
else:
    print('Failed to retrieve terms. Status code:', term_response.status_code)

print(upcoming_terms)
# all_course_details = {}

# for term in upcoming_terms:
#     TERM_CODE = term['code']
#     post_options['data']['term'] = TERM_CODE
#     search_options['params']['txt_term'] = TERM_CODE

#     # POST to search for courses under the term
#     post_response = requests.post(**post_options)

#     if post_response.status_code == 200:       
#         print(post_response.json())
#         search_response = requests.post(**search_options, allow_redirects=True)
#         if search_response.status_code == 200:
#             # Resolved
#             all_course_details.update(search_response.json())
#         else:
#             print('Failed to search for courses. Status code:', search_response.status_code)
#     else:
#         print('Failed to POST to search for term. Status code:', post_response.status_code)

# # Serializing json
# json_object = json.dumps(all_course_details, indent=4)
 
# # Writing to sample.json
# with open("all_courses.json", "w") as outfile:
#     outfile.write(json_object)

with open('all_courses.json') as f:
    data = json.load(f)

# Normalize the nested JSON data into a DataFrame
df = pd.json_normalize(data['data'])

# Extract faculty details
df['faculty_banner_id'] = df['faculty'].apply(lambda x: x[0]['bannerId'] if x else None)
df['faculty_displayName'] = df['faculty'].apply(lambda x: x[0]['displayName'] if x else None)
df['faculty_emailAddress'] = df['faculty'].apply(lambda x: x[0]['emailAddress'] if x else None)

# Select required columns
columns = ['id', 'term', 'termDesc', 'courseReferenceNumber', 
           'courseNumber', 'subject', 'subjectDescription', 
           'sequenceNumber', 'campusDescription', 'scheduleTypeDescription', 
           'courseTitle', 'creditHours', 'subjectCourse', 'faculty_banner_id', 
           'faculty_displayName', 'faculty_emailAddress']

# Create the normalized DataFrame with the selected columns
df_normalized = df[columns]
df_normalized['course_description'] = ''

print(df_normalized.shape)

# Function to perform the API request with retries and exponential backoff
def perform_api_request_with_retry(api_request_func, **kwargs):
    max_retries = 3  # Maximum number of retries
    base_delay = 1   # Base delay in seconds
    max_delay = 32   # Maximum delay in seconds

    for retry_count in range(max_retries):
        try:
            response = api_request_func(**kwargs)  # Perform the API request
            if response.status_code == 200:
                return response  # Return response if successful
            else:
                print(f"Request failed with status code {response.status_code}. Retrying...")
        except Exception as e:
            print(f"Request failed with exception: {e}. Retrying...")

        # Calculate exponential backoff delay
        delay = min(base_delay * 2 ** retry_count, max_delay)
        time.sleep(delay)

    print("Exceeded maximum number of retries. Request failed.")
    return None

for index, course in df_normalized.iterrows():
    course_description_options['params']['term'] = course['term']
    course_description_options['params']['courseReferenceNumber']= course['courseReferenceNumber']
    description_response = perform_api_request_with_retry(requests.post, **course_description_options)

    if description_response.status_code == 200:
        # Resolved
        df_normalized.at[index, 'course_description'] = description_response.content
        reset_response = perform_api_request_with_retry(requests.post, **reset_form_options)
        if reset_response.status_code != 200:
            print('Failed to reset search. Status code:', reset_response.status_code)
    else:
        print('Failed to get course description. Status code:', description_response.status_code)

print(df_normalized.head(10))
print(df_normalized.loc[4])

df_normalized.to_csv('banner_data.csv', index=True)