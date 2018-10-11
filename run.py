import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def notify(mesg):
    print(mesg.replace('\\n', '\n'))
    os.system('printf \"{}\" | /usr/local/bin/telegram-send --format markdown --config home-group.conf --stdin'.format(mesg))

def print_expiring_items(items, expiring_in_days):
    print_items(items, 'These items are expiring in the next \`{}\` days\\n'.format(expiring_in_days))

def print_deleted_items(items):
    print_items(items, "Removed these items from gsheet...\\n")

def print_error_items(items):
    print_items(items, "Warning these items does not have date or name\\n", False)

def print_items(items, header_mesg, sort=True):
    if len(items) > 0:
        if sort:
            items.sort(key=lambda r: datetime.datetime.strptime(r['DATE'], "%d/%m/%Y"))

        mesg = header_mesg

        for item in items:
            mesg += '{} | {}\\n'.format(item['DATE'], item['NAME'])
        
        notify(mesg)

def convert_to_datetime(str):
    return datetime.datetime.strptime(str, "%d/%m/%Y")

def check():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open("item expiry list").sheet1
    records = sheet.get_all_records()

    today = datetime.date.today()
    one_month_from_today = today + datetime.timedelta(days=31)
    one_week_from_today = today + datetime.timedelta(days=7)

    items_expiring_in_a_month = []
    items_expiring_in_a_week = []
    items_deleted = []
    items_without_date_or_name = []

    rows_to_delete = []

    for row, record in enumerate(records):
        if not record['DATE'] or not record['NAME']:
            items_without_date_or_name.append(record)
            continue
        
        item_date = convert_to_datetime(record['DATE']).date()
        
        if item_date <= one_month_from_today and record['NOTIFIED'] == '':
            items_expiring_in_a_month.append(record)
            # Sheet counts from 1 
            # Add additional 1 to skip header row
            sheet.update_cell(row + 2, 3, 'T')
        
        elif item_date <= one_week_from_today and record['NOTIFIED'] == 'T':
            items_expiring_in_a_week.append(record)
            sheet.update_cell(row + 2, 3, 'TT')
        
        elif record['NOTIFIED'] == 'TT':
            items_deleted.append(record)
            rows_to_delete.append(row)

    # Delete rows last and from larger row number to small row number to peserve correct row states
    for row in reversed(rows_to_delete):
        sheet.delete_row(row + 2)

    print_expiring_items(items_expiring_in_a_month, 31)
    print_expiring_items(items_expiring_in_a_week, 7)
    print_deleted_items(items_deleted)
    print_error_items(items_without_date_or_name)

    if (len(items_expiring_in_a_month) == 0 
        and len(items_expiring_in_a_week) == 0 
        and len(items_deleted) == 0 
        and len(items_without_date_or_name) == 0):
        notify('Nothing expiring. See you next week.\\nBye!')

if __name__ == '__main__':
    check()
