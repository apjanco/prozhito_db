from django.core.management.base import BaseCommand, CommandError
from prozhito_app.models import *
import mysql.connector
import tqdm

#for NLP
#import stanfordnlp
#from spacy_stanfordnlp import StanfordNLPLanguage
#from natasha import NamesExtractor
#from pymystem3 import Mystem

#for geocoding
from geopy.geocoders import Nominatim
from django.contrib.gis.geos import Point

#for sentiment
#from dostoevsky.tokenization import UDBaselineTokenizer, RegexTokenizer
#from dostoevsky.embeddings import SocialNetworkEmbeddings
#from dostoevsky.models import SocialNetworkModel


#wikipedia2vec for automatic entity extraction
#from wikipedia2vec import Wikipedia2Vec

def get_count(cursor, table):
    query = ("SELECT count(*) FROM {}".format(table))
    cursor.execute(query)
    for row in cursor:
        return row[0]

def load_persons(cursor):
    query = ("SELECT * FROM persons")
    cursor.execute(query)

    for row in tqdm.tqdm(cursor):
        Person.objects.update_or_create(
            id=row[0],
            first_name=row[1],
            family_name=row[2],
            patronymic=row[3],
            nickname=row[4],
            edition=row[5],
            # birthDay
            # deathDay
            birth_date=row[8],
            death_date=row[9],
            # ageAround
            info=row[11],
            additional_info=row[12],
            # forVolunteers
            wiki=row[14],
            # avatar
            # countDiaries
            # user
            gender=row[18],
            # updates
            # createdDate
        )


def load_diaries(cursor):
    query = ("SELECT * FROM diary")
    cursor.execute(query)

    for row in tqdm.tqdm(cursor):

        Diary.objects.update_or_create(
            id=row[0],
            author=Person.objects.get_or_create(id=row[1])[0],
            no_entries=row[3],
            first_note=row[4],
            last_note=row[5],
            )


def load_tags(cursor):
    query = ('SELECT * from tags')
    cursor.execute(query)

    for row in tqdm.tqdm(cursor):
        id = row[0]
        text = row[1]
        type = row[2]

        if type == 1:  # keyword
            Keyword.objects.update_or_create(
                name=text,
            )

        if type == 2:  # location
            Place.objects.update_or_create(
                name=text,
            )
            #TODO add logic to get wikipedia link and geocoding
            #wiki
            #gis

        if type == 3:  # person
            """There are too many possible combinations of names to create stable rules.
            I have created a rule where imiia otchestvo familiia appear.  Otherwise, with 
            two names, it is impossible to know if it is imiia otchestvo or imiia familiia.
            Similarly, I have chosen to exclude abbreviations even when we have three letters, 
            they would have to be manually matched with a full name. I see no reason to add
            data that cannot be connected to a full person profile.   Testing with Natasha
            proved this not to be an effective solution. 
            """

            if '.' in text:
                pass

            else:
                if len(text.split(' ')) == 3:

                    #check if exiting Person object exist
                    person = Person.objects.filter(
                        first_name=text.split(' ')[0].strip(),
                        patronymic=text.split(' ')[1].strip(),
                        family_name=text.split(' ')[2].strip(),
                    )

                    if len(person) == 0:
                        Person.objects.update_or_create(
                            first_name=text.split(' ')[0].strip(),
                            patronymic=text.split(' ')[1].strip(),
                            family_name=text.split(' ')[2].strip(),
                            from_tags=True
                        )


def load_notes(cursor):
    query = ('select * from notes n join diary d on d.id = n.diary ')
    cursor.execute(query)

    for row in tqdm.tqdm(cursor):

        if row[3] is not None:
            if not row[3].isoformat():
                print('[*] Error note #{}'.format(row[0]))
                date_start = None

            if row[4] == '0000-00-00':
                date_end = None

        date_start = row[3]
        date_end = row[4]

        try:
            author = Person.objects.get(pk=row[11])

            Entry.objects.update_or_create(
                id=row[0],
                diary=row[1],
                text=row[2],
                lemmatized='',
                date_start=date_start,
                date_end=date_end,
                author=author,
                )
        except Exception as e:
            print(e, 'note_id: ', row[0],'person_id: ', row[11])

def update_entries_with_tags(cursor):
    query = ('select * from tags_notes tn join tags t on t.id = tn.tag')
    cursor.execute(query)

    for row in tqdm.tqdm(cursor):
        note_id = row[0]
        name = row[3]
        type = row[4]

        try:
            if type == 1:
                entry = Entry.objects.get(id=note_id)
                keyword = Keyword.objects.get_or_create(name=name)[0]
                entry.keywords.add(keyword)
                entry.save()

            if type == 2:
                entry = Entry.objects.get(id=note_id)
                place = Place.objects.get_or_create(name=name)[0]
                entry.places.add(place)

            #if type == 3:
            #   entry = Entry.objects.get(pk=note_id)
            #   person = Person.objects.
            #  This could get messy, need to give it some though

        except Exception as e:
            print(e, note_id)
        #For each person, place, keyword update existing entry relationships


def lemmatize_texts(lemmatizer):
    entries = Entry.objects.filter(lemmatized='')

    if lemmatizer == 'stanford':
        texts = [(entry.text, entry.id) for entry in entries]
        snlp = stanfordnlp.Pipeline(lang='ru')
        nlp = StanfordNLPLanguage(snlp)
        for doc in tqdm.tqdm(nlp.pipe(texts, batch_size=100, as_tuples=True, disable=["tagger", "parser", "pos", "depparse"])):
            id = doc[1]
            lemmatized = ' '.join([token.lemma_ for token in doc[0]])
            entry = Entry.objects.get(id=id)
            entry.lemmatized = lemmatized
            entry.save()
    if lemmatizer == 'mystem':
        m = Mystem()
        for entry in tqdm.tqdm(entries):
            lemmas = m.lemmatize(entry.text)
            lemmatized = ''.join(lemmas)
            entry = Entry.objects.get(id=entry.id)
            entry.lemmatized = lemmatized
            entry.save()


def geocode_places():
    places = Place.objects.all()
    for place in tqdm.tqdm(places):
        geolocator = Nominatim(user_agent="prozhito_db")
        location = geolocator.geocode(place.name)
        if location:
            pnt = Point(location.longitude, location.latitude)
            # add gis
            place.gis = pnt
            place.save()


def geocode_entries():
    snlp = stanfordnlp.Pipeline(lang='ru')
    nlp = StanfordNLPLanguage(snlp)
    entries = Entry.objects.all()
    for entry in tqdm.tqdm(entries):
        doc = nlp(entry.text)
        words = [token.text for token in doc if token.is_punct is False and token.is_stop is False]
        for word in words:
            geolocator = Nominatim(user_agent="prozhito_db")
            location = geolocator.geocode(word)
            if location:
                print(location)
                """
                place = Place.objects.get_or_create(name=word, gis=Point(location.longitude, location.latitude))
                entry.places.add(place[0])
                entry.save()
                print("added ", place[0].name, 'to', entry.id)
                """

def names_extractor():
    entries = Entry.objects.all()
    for entry in tqdm.tqdm(entries):
        text = entry.text
        extractor = NamesExtractor()
        matches = extractor(text)
        if not len(matches) == 0:
            for match in matches:
                if match.fact.first and match.fact.middle and match.fact.last:
                    person = Person.objects.get_or_create(first_name=match.fact.first, patronymic=match.fact.middle, family_name=match.fact.last, from_natasha=True)
                    entry.people.add(person[0])
                    entry.save()
                    print(f'[*] added person {match.fact.first} {match.fact.middle} {match.fact.last} ')

def detect_sentiment():
    tokenizer = UDBaselineTokenizer() or RegexTokenizer()
    embeddings_container = SocialNetworkEmbeddings()
    model = SocialNetworkModel(
        tokenizer=tokenizer,
        embeddings_container=embeddings_container,
        lemmatize=False,
    )
    entries = Entry.objects.filter(sentiment=None)
    for entry in tqdm.tqdm(entries):
        try:
            results = model.predict([entry.text])
            entry.sentiment = results[0]
            entry.save()
        except Exception as e:
            print(e)

def nearest_entities(text):

    ents = [i for i in text]

def wikipedia2vec_entities():
    wiki2vec = Wikipedia2Vec.load(MODEL_FILE)
    entries = Entry.objects.all()
    for entry in entries:
        entities = "" #TODO find entities on tokens or full text?
        for entity in entities:
            entry.keywords.add(Keyword.objects.get_or_create(name=entity.title))
            entry.save()

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

        #TODO Add function to load from sql file, create database, then read from that db
        #load_sql_file()

        self.stdout.write(self.style.SUCCESS('[*] loading {} persons'.format(get_count(cursor, 'persons'))))
        #load_persons(cursor)

        self.stdout.write(self.style.SUCCESS('[*] loading {} tags'.format(get_count(cursor, 'tags'))))
        #load_tags(cursor)

        self.stdout.write(self.style.SUCCESS('[*] loading {} diary entries'.format(get_count(cursor, 'notes'))))
        #load_notes(cursor)

        self.stdout.write(self.style.SUCCESS('[*] loading {} diaries'.format(get_count(cursor, 'diary'))))
        load_diaries(cursor)

        self.stdout.write(self.style.SUCCESS('[*] updating {} entry tags'.format(get_count(cursor, 'tags_notes'))))
        #update_entries_with_tags(cursor)

        self.stdout.write(self.style.SUCCESS('[*] lemmatizing text of {} diary entries'.format(str(Entry.objects.filter(lemmatized='').count()))))
        #lemmatize_texts('mystem')

        self.stdout.write(self.style.SUCCESS('[*] geocoding {} places'.format(Place.objects.all().count())))
        #geocode_places()

        self.stdout.write(self.style.SUCCESS('[*] extracting names with Natasha'))
        #names_extractor()
        #TODO cluster and remove redundant Natasha persons

        self.stdout.write(self.style.SUCCESS('[*] detecting sentiment with Dostoevsky'))
        #detect_sentiment()

        self.stdout.write(self.style.SUCCESS('[*] geocoding text of all diary entries'))
        #geocode_entries()
        #auto_extract_persons_keywords_places()
        #self.stdout.write(self.style.SUCCESS(f'[*] updated entry tags'))



        #update_wikilinks()
        #self.stdout.write(self.style.SUCCESS(f'[*] updated entry tags'))

