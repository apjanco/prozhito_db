from django.core.management.base import BaseCommand, CommandError
from prozhito_app.models import *
import mysql.connector

def load_persons(cursor):
    query = ("SELECT * FROM persons")
    cursor.execute(query)

    for row in cursor:
        id = row[0]
        firstname = row[1]
        lastname = row[2]
        thirdname = row[3]
        nickname = row[4]
        edition = row[5]
        #birthDay
        #deathDay
        birthday = row[8]
        deathday = row[9]
        #ageAround
        info = row[11]
        additional_info = row[12]
        #forVolunteers
        wikilink = row[14]
        #avatar
        #countDiaries
        #user
        gender = row[18]
        #updates
        #createdDate

        print(id, firstname, lastname, thirdname, nickname, edition, birthday, deathday, info, additional_info, wikilink, gender,)

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('db_name', nargs='+', type=str)

    def handle(self, *args, **options):
        db_name = options['db_name'][0]
        self.stdout.write(self.style.SUCCESS(f'is this your db_name? {db_name}'))

        config = {
            'user': 'prozhito_db',
            'password': '8,rkT5?:p$S3g2U/',
            'host': '127.0.0.1',
            'database': 'prozhito',
            'raise_on_warnings': True
        }

        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        load_persons(cursor)

        #process_tags(cursor)

