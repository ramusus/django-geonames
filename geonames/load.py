import bz2, gzip, os, zipfile
from datetime import datetime

from django.db import transaction

from models import Admin1Code, Admin2Code, TimeZone, Geoname, Alternate

GEONAMES_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

def txt_lengths(txt_file):
    fh = open(os.path.join(GEONAMES_DATA, txt_file))
    lengths = {}
    for line in fh:
        splits = line.split('\t')
        for i, col in enumerate(splits):
            n = len(col.strip())
            if not i in lengths:
                lengths[i] = [n]
            else:
                lengths[i].append(n)
    
    cols = lengths.keys()
    cols.sort()
    for col in cols:
        print '%d: %d' % (col, max(lengths[col]))

def clean(sarr):
    return [s.strip().decode('utf8') for s in sarr]

@transaction.commit_on_success
def run():
    # Loading the Admin1Code models
    fh = open(os.path.join(GEONAMES_DATA, 'admin1Codes.txt'))
    fields = ('code', 'name')
    for line in fh:
        splits = line.split('\t')
        kwargs = dict(zip(fields, clean(splits)))
        admin1 = Admin1Code.objects.create(**kwargs)

    # Loading the Admin2Code models
    fh = open(os.path.join(GEONAMES_DATA, 'admin2Codes.txt'))
    fields = ('code', 'name', 'ascii', 'geonameid')
    for line in fh:
        splits = line.split('\t')
        kwargs = dict(zip(fields, clean(splits)))
        for key in ('ascii', 'geonameid'): kwargs.pop(key)
        admin2 = Admin2Code.objects.create(**kwargs)

    # Loading the TimeZone models.
    fh = open(os.path.join(GEONAMES_DATA, 'timeZones.txt'))
    fields = ('tzid', 'gmt_offset', 'dst_offset')
    header = fh.next()
    for line in fh:
        splits = line.split('\t')
        kwargs = dict(zip(fields, clean(splits)))
        tz = TimeZone.objects.create(**kwargs)    
