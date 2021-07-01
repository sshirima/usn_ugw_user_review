import pandas as pd
import pathlib
from datetime import datetime

def _get_userinput_filename(dir, user_message, error_message):

    p_filename = input(user_message)

    if not dir == '':
        return dir+'/'+p_filename

    p_filepath = pathlib.Path(p_filename)

    while not p_filepath.suffix == '.csv' and not p_filepath.exists():

        #print('Error: File {} does not exist'.format(p_filename))
        print(error_message)

        p_filename = input(
            'Enter previous user review for {}: '.format(node_name))

        p_filepath = pathlib.Path(p_filename)

    if dir == '':
        return p_filename

    return p_filename

def get_previous_user_review(node_name):

    p_filename = _get_userinput_filename('user_reviews', 'Enter previous user review for {}: '.format(
        node_name), 'Error: File does not exist or is not csv file type')

    p_user_review = pd.read_csv(p_filename, skip_blank_lines=True)

    p_user_review.set_index(['Username'])

    return p_user_review

def get_operation_logs(filename):

    operation_logs = pd.read_csv(
        filename.strip(), skip_blank_lines=True, header=5)

    operation_logs['Start Time'] = pd.to_datetime(operation_logs['Start Time'])

    return operation_logs


def get_login_requests(operation_logs, node_name):

    logins_request = operation_logs[(operation_logs['NE Name'].str.contains(node_name)) & (
        operation_logs['Command'].str.contains('LGI REQUEST')) & (operation_logs['Result'] == 'Succeeded')]

    logins_request_sorted = logins_request[['User', 'Start Time']].sort_values(
        by=['User', 'Start Time']).groupby('User', as_index=False).last()

    logins_request_sorted = logins_request_sorted.rename(
        columns={'User': 'Username', 'Start Time': 'Last Logon'})

    logins_request_sorted.set_index(['Username'])

    return logins_request_sorted


def get_password_change_requests(operation_logs):

    password_change = operation_logs[(operation_logs['Command'].str.contains('MOD PWD')) & (operation_logs['Result'] == 'Succeeded')]

    password_change_sorted = password_change[['User', 'Start Time']].sort_values(by=['User', 'Start Time']).groupby('User', as_index=False).last()

    password_change_sorted = password_change_sorted.rename(columns={'User': 'Username', 'Start Time': 'Last Password Change'})

    password_change_sorted.set_index(['Username'])

    return password_change_sorted


def get_account_status(login_requests, previous_user_review, review_date):

    review_date = datetime.strptime(review_date, '%Y-%m-%d')

    user_review = login_requests.combine_first(
        previous_user_review).reset_index()

    user_review['Last Logon'] = pd.to_datetime(user_review['Last Logon'])

    #print((review_date - user_review['Last Logon']).dt.days)
    user_review.loc[((review_date - user_review['Last Logon']
                      ).dt.days <= 30), 'Account Status'] = 'Active'

    user_review.loc[((review_date - user_review['Last Logon']
                      ).dt.days > 30), 'Account Status'] = 'Inactive'

    return user_review


def get_password_status(password_change_requests, previous_user_review, review_date):

    #print(password_change_requests)

    review_date = datetime.strptime(review_date, '%Y-%m-%d')

    #user_review = password_change_requests.combine_first(previous_user_review).reset_index()
    updated_date = lambda pre, now: now if prev < now else prev 

    user_review = previous_user_review.combine(password_change_requests, updated_date(previous_user_review['Last Password Change'], 
                                                    password_change_requests['Last Password Change']), overwrite=False).reset_index()
    
    print(user_review[['Username', 'Last Password Change']])

    user_review['Last Password Change'] = pd.to_datetime(user_review['Last Password Change'])

    #print((review_date - user_review['Last Password Change']).dt.days)

    user_review.loc[((review_date - user_review['Last Password Change']
                      ).dt.days <= 60), 'Password Status'] = 'Active'

    user_review.loc[((review_date - user_review['Last Password Change']
                      ).dt.days > 60), 'Password Status'] = 'Inactive'

    return user_review


def update_account_status(node_name, operation_logs):

    previous_user_review = _get_previous_user_review(node_name)

    login_requests = _get_login_requests(operation_logs, node_name)

    user_review = _get_account_status(login_requests, previous_user_review, review_date)

    password_change_requests = _get_password_change_requests(operation_logs)

    user_review = _get_password_status(password_change_requests, user_review, review_date)

    return user_review


def export_user_review_file(user_review, node_name):
    now = datetime.now()

    #print(user_review[['Username', 'Last Logon', 'Account Status']])

    f_name = 'output/{}_{}_{}_{}_{}.csv'.format(now.year, now.month, now.day, str(
        now.hour)+str(now.minute)+str(now.second), node_name.upper())

    user_review.to_csv(f_name, index=False)


#filename = _get_userinput_filename(
#    'logs', 'Enter the operation logs file name: ', 'Error: File does not exist or is not csv file type')
#
#operation_logs = _get_operation_logs(filename)
#
##node_type = _get_userinput_nodetype('Enter node type: ', 'Error: Type does not exist')
#
#review_date = '2021-05-31'
#
#user_review_kwale_ugw = _update_account_status('Kwale_UGW', operation_logs)
#user_review_mbezi_ugw = _update_account_status('Mbezi_UGW', operation_logs)
#user_review_kwale_usn = _update_account_status('KwaleUSN9810', operation_logs)
#user_review_mbezi_usn = _update_account_status('MbeziUS9810', operation_logs)
#
#_export_user_review_file(user_review_kwale_ugw, 'Kwale_UGW')
#_export_user_review_file(user_review_mbezi_ugw, 'Mbezi_UGW')
#_export_user_review_file(user_review_kwale_usn, 'KwaleUSN9810')
#_export_user_review_file(user_review_mbezi_ugw, 'MbeziUS9810')
