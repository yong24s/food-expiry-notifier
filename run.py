import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def notify(mesg):
    print(mesg)
    os.system('telegram-send --config home-group.conf\"' + mesg + '\"')

def check():
    scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open("item expiry list").sheet1
    records = sheet.get_all_records()

    # We need to preserve row info to update rows.
    # records.sort(key=lambda r: datetime.datetime.strptime(r['DATE'], "%d/%m/%Y"))

    # Assume that the script will be executed on Monday, then get the date of that day + 6 days
    today = datetime.date.today()
    six_days_after_today = today + datetime.timedelta(days=6)

    items = []

    for row, record in enumerate(records):
        item_date = datetime.datetime.strptime(record['DATE'], "%d/%m/%Y").date()

        if item_date < six_days_after_today and record['NOTIFIED'] is not 'T':
            items.append(record)
            # Sheet counts from 1 
            # Add additional 1 to skip header row
            sheet.update_cell(row + 2, 3, 'T')

    if len(items) > 0:
        mesg = 'Hey! These items are expiring...\n'
        
        for item in items:
            mesg += '{} | {}\n'.format(item['DATE'], item['NAME'])
        
        notify(mesg)

if __name__ == '__main__':
    check()
