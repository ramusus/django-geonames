from optparse import make_option
import datetime, os, sys
import urllib, urllib2, urlparse
import re

from django.db import connection, models
from django.core.management import call_command, sql, color
from django.core.management.base import NoArgsCommand
from django.conf import settings
from compress_geonames import GEONAMES_DATA

GEONAMES_DUMPS_URL = 'http://download.geonames.org/export/dump/'

def download(url, filepath=False):
    """
    Copy the contents of a file from a given URL to a local file.
    """
    filepath = filepath or url.split('/')[-1]

    web_file = urllib.urlopen(url)

    dir = '/'.join(filepath.split('/')[:-1])
    if not os.path.isdir(dir):
        os.makedirs(dir)

    # check size of files
    web_file_size = web_file.info().getheaders("Content-Length")[0]
    if os.path.isfile(filepath):
        existing_file = open(filepath, "r")
        existing_file_size = len(existing_file.read())
        print existing_file_size, web_file_size
        if existing_file_size == web_file_size:
            existing_file_size.close()
            return

    local_file = open(filepath, 'w')
    local_file.write(web_file.read())
    web_file.close()
    local_file.close()

class Command(NoArgsCommand):
    help = 'Download all data files from geonames to data dir.'

    option_list = NoArgsCommand.option_list + (
        make_option('-t', '--time', action='store_true', dest='time', default=False,
                    help='Print the total time in running this command'),
        make_option('--country', action='store', dest='country', default=False,
                    help='Download only data for specified country.'),
        make_option('--no-alternates', action='store_true', dest='no_alternates', default=False,
                    help='Disable loading of the Geonames alternate names data.'),
        make_option('--no-geonames', action='store_true', dest='no_geonames', default=False,
                    help='Disable loading of the Geonames data.'),
        )

    def handle_noargs(self, **options):
        if options['time']:
            start_time = datetime.datetime.now()

        response = urllib2.urlopen(urllib2.Request(url=GEONAMES_DUMPS_URL))
        files = re.findall(r'\<a href="(.+\.(?:txt|zip))"\>', response.read())
        for file in files:

            if options['country'] and file != '%s.zip' % options['country'] \
                or options['no_geonames'] and file == 'allCountries.zip' \
                or options['no_alternates'] and file == 'alternateNames.zip' \
                or not options['country'] and len(file) == 6:
                    continue

            print '\nStart download "%s" file' % file
            download(urlparse.urljoin(GEONAMES_DUMPS_URL, file), os.path.join(GEONAMES_DATA, file))

        if options['time']:
            print '\nCompleted in %s' % (datetime.datetime.now() - start_time)