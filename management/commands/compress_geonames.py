import datetime, gzip, os, sys, zipfile
from optparse import make_option

from django.core.management.base import NoArgsCommand

from geonames import models
GEONAMES_DATA = os.path.abspath(os.path.join(os.path.dirname(models.__file__), 'data'))

class Command(NoArgsCommand):
    
    option_list = NoArgsCommand.option_list + (
        make_option('-t', '--time', action='store_true', dest='time', default=False,
                    help='Print the total time in running this command'),
        make_option('-l', '--lengths', action='store_true', dest='lengths', default=False,
                    help='Print the lengths for each of the fields.'),
        make_option('--no-countries', action='store_true', dest='no_countries', default=False,
                    help='Do not perform compression on allCountries.zip'),
        make_option('--no-alternates', action='store_true', dest='no_alternates', default=False,
                    help='Do not perform compression on alternateNames.zip'),
                    )

    clear_line = chr(27) + '[2K' + chr(27) +'[G'

    def allCountries(self, **options):
        zf = zipfile.ZipFile(os.path.join(GEONAMES_DATA, 'allCountries.zip'))
        gzf = gzip.GzipFile(os.path.join(GEONAMES_DATA, 'allCountries.gz'), 'w')

        in_fields = ['geonameid', 'name', 'asciiname', 'alternates', 'latitude', 'longitude',
                     'fclass', 'fcode', 'country_code', 'cc2', 
                     'admin1', 'admin2', 'admin3', 'admin4',
                     'population', 'elevation', 'topo', 'timezone', 'mod_date']
        out_fields = [f for f in in_fields if not f in ('latitude', 'longitude', 'asciiname')]
        len_fields = ['name', 'asciiname', 'alternates', 'fclass', 'fcode', 'country_code',
                      'cc2', 'admin1', 'admin2', 'admin3', 'admin4', 'timezone']
        if options['lengths']: lengths = dict([(f, 0) for f in len_fields])

        contents = zf.read('allCountries.txt').split('\n')
        num_lines = len(contents)
        for i, line in enumerate(contents):
            if line:
                row = dict(zip(in_fields, map(str.strip, line.split('\t'))))
                if options['lengths']:
                    for k in len_fields: lengths[k] = max(len(row[k]), lengths[k])

                try:
                    # Setting integers to 0 so they won't have to be NULL.
                    for key in ('population', 'elevation', 'topo'):
                        if not row[key]: row[key] = '0'  
                
                    # Getting the EWKT for the point -- has to be EWKT or else
                    # the insertion of the point will raise a constraint error for
                    # for a non-matching ID.
                    wkt = 'SRID=4326;POINT(%s %s)' % (row['longitude'], row['latitude'])
                except KeyError:
                    sys.stderr.write('Invalid row (line %d):\n' % i)
                    sys.stderr.write('%s\n' % str(row))
                else:
                    new_line = '\t'.join([row[k] for k in out_fields])
                    new_line += '\t%s\n' % wkt
                    gzf.write(new_line)

            if i % 10000 == 0:
                sys.stdout.write(self.clear_line)
                sys.stdout.write('Compressing allCountries.txt: %.2f%% (%d/%d)' % ( (100. * i) / num_lines, i, num_lines))
                sys.stdout.flush()

        gzf.close()

        sys.stdout.write('\n')

        if options['lengths']:
            for fld in len_fields:
                sys.stdout.write('%s:\t%d\n' % (fld, lengths[fld]))

    def alternateNames(self, **options):
        zf = zipfile.ZipFile(os.path.join(GEONAMES_DATA, 'alternateNames.zip'))
        gzf = gzip.GzipFile(os.path.join(GEONAMES_DATA, 'alternateNames.gz'), 'w')

        in_fields = ['alternateid', 'geoname_id', 'isolanguage', 'variant', 'preferred', 'short']
        bool_fields = ['preferred', 'short']
        len_fields = ['isolanguage', 'variant']
        out_fields = in_fields
        if options['lengths']: lengths = dict([(f, 0) for f in len_fields])

        contents = zf.read('alternateNames.txt').split('\n')
        num_lines = len(contents)
        for i, line in enumerate(contents):
            if line:
                row = dict(zip(in_fields, map(str.strip, line.split('\t'))))
                for bool_field in bool_fields:
                    if row[bool_field]:
                        row[bool_field] = '1'
                    else:
                        row[bool_field] = '0'
                if options['lengths']:
                    for k in len_fields: lengths[k] = max(len(row[k]), lengths[k])
                new_line = '\t'.join([row[k] for k in out_fields])
                new_line += '\n'
                gzf.write(new_line)

                if i % 10000 == 0:
                    sys.stdout.write(self.clear_line)
                    sys.stdout.write('Compressing alternateNames.txt: %.2f%% (%d/%d)' % ( (100. * i) / num_lines, i, num_lines))
                    sys.stdout.flush()

        gzf.close()

        sys.stdout.write('\n')

        if options['lengths']:
            for fld in len_fields:
                sys.stdout.write('%s:\t%d\n' % (fld, lengths[fld]))


    def handle_noargs(self, **options):
        if options['time']:
            start_time = datetime.datetime.now()

        if not options['no_countries']:
            self.allCountries(**options)

        if not options['no_alternates']:
            self.alternateNames(**options)

        if options['time']: 
            sys.stdout.write('\nCompleted in %s\n' % (datetime.datetime.now() - start_time))
