from bucket_operations import read_csv_from_bucket, upload_csv_to_gcs
from datetime import datetime
import pandas as pd


def update_volunteer_insights(location, details):
    insights = read_csv_from_bucket('missing_people_search',
                                    'person1234/volunteer_updates_more_mocked.csv')
    df = pd.DataFrame(insights[1:], columns=insights[0])
    new_update = {'Update_ID': int(df['Update_ID'].max()) + 1,
                  'Volunteer_Name': 'Nataliya',
                  'Update_Date': datetime.now().strftime("%m/%d/%Y  %I:%M:%S %p"),
                  'Location_Reported': location,
                  'Details': details,
                  'Follow_Up_Action': 'search'}
    new_update = pd.DataFrame([new_update])
    df = pd.concat([df, new_update], ignore_index=True)
    upload_csv_to_gcs('missing_people_search',
                     'person1234/volunteer_updates_more_mocked.csv',
                      df)
    return True

