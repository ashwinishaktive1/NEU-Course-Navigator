"""
Loading data into tabular form from the NEU Banner website using the NU Banner API.
This data (in .csv) format can now be used as context for the RAG models.

Author: Ashwini Shaktivel Kumar
"""
import requests
import json
import pandas as pd
import time

"""
Defining options (arguments) for the API requests
"""
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
    'pageMaxSize': '2000', # Get at max 2000 results for every term 
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

"""
Retrieving available terms and their codes from the Banner
"""
# Send the request to retrieve terms:
term_response = requests.get(**term_options)

# Check if the request was successful:
if term_response.status_code == 200:
    upcoming_terms = term_response.json()
    # Setting cookies:
    post_options['cookies'] = term_response.cookies
    search_options['cookies'] = term_response.cookies
    reset_form_options['cookies'] = term_response.cookies
else:
    print('Failed to retrieve terms. Status code:', term_response.status_code)

print(upcoming_terms)

"""
Gathering courses and their descriptive features into a combined JSON file.
"""
all_course_details = []

# Looping through every term:
for term in upcoming_terms:
    TERM_CODE = term['code']
    post_options['data']['term'] = TERM_CODE
    search_options['params']['txt_term'] = TERM_CODE

    # POST to search for courses under the term:
    post_response = requests.post(**post_options)

    # If successful:
    if post_response.status_code == 200:       
        print(post_response.json())
        search_response = requests.post(**search_options, allow_redirects=True)
        if search_response.status_code == 200:
            # Append to the all_course_details list:
            all_course_details.append(search_response.json())
        else:
            print('Failed to search for courses. Status code:', search_response.status_code)
    else:
        print('Failed to POST to search for term. Status code:', post_response.status_code)

# Serializing json:
json_object = json.dumps(all_course_details, indent=4)
 
# Writing to all_courses.json:
with open("all_courses.json", "w") as outfile:
    outfile.write(json_object)

# Opening the json file:
with open('all_courses.json') as f:
    data = json.load(f)

"""
Normalizing and transforming the nested JSON file to a Pandas dataframe. 
Using only necessary columns. 
"""
# List to store normalized data:
normalized_data = []

# Extract relevant information from each JSON object:
for obj in data:
    for course_obj in obj["data"]:
        course_info = {
            "id": course_obj["id"],
            "term": course_obj["term"],
            "termDesc": course_obj["termDesc"],
            "courseReferenceNumber": course_obj["courseReferenceNumber"],
            "courseNumber": course_obj["courseNumber"],
            "subject": course_obj["subject"],
            "subjectDescription": course_obj["subjectDescription"],
            "sequenceNumber": course_obj["sequenceNumber"],
            "campusDescription": course_obj["campusDescription"],
            "scheduleTypeDescription": course_obj["scheduleTypeDescription"],
            "courseTitle": course_obj["courseTitle"],
            "creditHours": course_obj["creditHours"],
            "subjectCourse": course_obj["subjectCourse"],
            "faculty_banner_id": None,
            "faculty_displayName": None,
            "faculty_emailAddress": None
        }
        
        # Check if the "faculty" list is not empty:
        if course_obj["faculty"]:
            course_info["faculty_banner_id"] = course_obj["faculty"][0]["bannerId"]
            course_info["faculty_displayName"] = course_obj["faculty"][0]["displayName"]
            course_info["faculty_emailAddress"] = course_obj["faculty"][0]["emailAddress"]
        
        normalized_data.append(course_info)

# Convert the list of dictionaries to a DataFrame:
print(len(normalized_data))
df_normalized = pd.DataFrame(normalized_data)
df_normalized['course_description'] = ''
print("Size of the dataframe:", df_normalized.shape)

"""
Getting course description using the getCourseDescription() POST request 
for every CRN in the terms. 
Adding the course description as a column. 
"""
# Function to perform the API request with retries and exponential backoff
def perform_api_request_with_retry(api_request_func, **kwargs):
    """
        Parameters
        ----------
        api_request_func : method
            The API request method (POST/GET)
        options : **kwargs
            The options (arguments) necessary for the request 
        
        Raises
        ------
        Exception
            If response is not successful.
    """
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

# Looping through every course in the normalized dataframe:
for index, course in df_normalized.iterrows():
    # Updating term and CRN options for the course description retrieval:
    course_description_options['params']['term'] = course['term']
    course_description_options['params']['courseReferenceNumber']= course['courseReferenceNumber']
    description_response = perform_api_request_with_retry(requests.post, **course_description_options)

    # If course description available after successful retries:
    if description_response is not None:
        if description_response.status_code == 200:
            # Adding course description from the response content:
            df_normalized.at[index, 'course_description'] = description_response.content
            # Resetting the search session:
            reset_response = perform_api_request_with_retry(requests.post, **reset_form_options)
            if reset_response.status_code != 200:
                print('Failed to reset search. Status code:', reset_response.status_code)
    else:
        # Empty course description if unavailable:
        df_normalized.at[index, 'course_description'] = ''
        print('Failed to get course description.', course['courseReferenceNumber'])

"""
Writing to a csv file
"""
df_normalized.to_csv('banner_data.csv', index=True)