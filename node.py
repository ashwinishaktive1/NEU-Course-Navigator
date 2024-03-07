import requests
import json

# Define the constants
SUBJECT = 'CS'
COURSE_NUMBER = '5004'
CRN = '52788'

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
    'courseReferenceNumber': CRN
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
    print(term_response.json())
    
    # Set term code
    TERM_CODE = '202450'
    post_options['data']['term'] = TERM_CODE
    search_options['params']['txt_term'] = TERM_CODE
    course_description_options['params']['term'] = TERM_CODE
    subject_search_options['params']['term'] = TERM_CODE

    subjects_response = requests.get(**subject_search_options)

    if subjects_response.status_code == 200:
        print('Subjects retrieved:', subjects_response.json())
    else:
        print('Failed to get course description. Status code:', subjects_response.status_code)

    # Set cookies
    # cookiejar = requests.cookies.RequestsCookieJar()
    # for cookie in term_response.headers['Set-Cookie'].split(','):
    #     cookiejar.set(*cookie.strip().split(';', 1))

    post_options['cookies'] = term_response.cookies
    search_options['cookies'] = term_response.cookies
    reset_form_options['cookies'] = term_response.cookies

    # POST to search for courses under the term
    post_response = requests.post(**post_options)

    if post_response.status_code == 200:
        print(post_response.json())

        # Assume it worked
        search_response = requests.post(**search_options, allow_redirects=True)
        
        if search_response.status_code == 200:
            # Resolved
            print(search_response.content)
            # print(json.dumps(search_response.json(), indent=2))
        else:
            print('Failed to search for courses. Status code:', search_response.status_code)

        description_response = requests.post(**course_description_options)

        if description_response.status_code == 200:
            # Resolved
            print(description_response.content)
            # reset_response = requests.post(**reset_form_options)
        else:
            print('Failed to get course description. Status code:', description_response.status_code)
    else:
        print('Failed to POST to search for term. Status code:', post_response.status_code)
else:
    print('Failed to retrieve terms. Status code:', term_response.status_code)
