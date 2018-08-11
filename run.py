import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def notify(mesg):
    print(mesg)
    os.system('telegram-send --format markdown --config home-group.conf \"' + mesg + '\"')

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
    items_removed = []

    for row, record in enumerate(records):
        item_date = datetime.datetime.strptime(record['DATE'], "%d/%m/%Y").date()

        if item_date <= one_month_from_today and record['NOTIFIED'] is not 'T':
            items_expiring_in_a_month.append(record)
            # Sheet counts from 1 
            # Add additional 1 to skip header row
            sheet.update_cell(row + 2, 3, 'T')
        
        elif item_date <= one_week_from_today and record['NOTIFIED'] is 'T':
            items_expiring_in_a_week.append(record)
            sheet.update_cell(row + 2, 3, 'TT')
        
        elif record['NOTIFIED'] is 'TT':
            items_removed.append(record)
            sheet.delete_row(row + 2)

    if len(items_expiring_in_a_month) > 0:
        mesg = 'Hey! These items are expiring in the next \`31\` days\n'
        
        for i, item in enumerate(items_expiring_in_a_month):
            if i % 2 == 0: mesg += '\`\`\`'
            mesg += '{} | {}\n'.format(item['DATE'], item['NAME'])
            if i % 2 == 0: mesg += '\`\`\`'

        notify(mesg)

    if len(one_week_from_today) > 0:
        mesg = 'These items are expiring in the next \`7\` days\n'
        
        for i, item in enumerate(one_week_from_today):
            if i % 2 == 0: mesg += '\`\`\`'
            mesg += '{} | {}\n'.format(item['DATE'], item['NAME'])
            if i % 2 == 0: mesg += '\`\`\`'

        notify(mesg)

if __name__ == '__main__':
    check()
