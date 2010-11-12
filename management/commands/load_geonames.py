import datetime, os, sys
from optparse import make_option

from django.db import connection, models
from django.core.management import call_command, sql, color
from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.contrib.gis.db.backend.postgis.creation import get_cmd_options

from geonames import models as m
Alternate = m.Alternate
Geoname = m.Geoname
GEONAMES_DATA = os.path.abspath(os.path.join(os.path.dirname(m.__file__), 'data'))

class Command(NoArgsCommand):
    
    option_list = NoArgsCommand.option_list + (
        make_option('-t', '--time', action='store_true', dest='time', default=False,
                    help='Print the total time in running this command'),
        make_option('--no-alternates', action='store_true', dest='no_alternates', default=False,
                    help='Disable loading of the Geonames alternate names data.'),
        make_option('--no-geonames', action='store_true', dest='no_geonames', default=False,
                    help='Disable loading of the Geonames data.'),
        )

    def handle_noargs(self, **options):
        if options['time']: start_time = datetime.datetime.now()

        # Making sure the db tables exist.
        call_command('syncdb')
        db_table = Geoname._meta.db_table

        db_opts = get_cmd_options(settings.DATABASE_NAME)

        fromfile_cmd = 'psql %(db_opts)s -f %(sql_file)s'
        fromfile_args = {'db_opts' : db_opts,
                         }
        
        ### COPY'ing into the Geonames table ###

        # Executing a shell command that pipes the unzipped data to PostgreSQL
        # using the `COPY` directive.  This builds the database directly from
        # the file made by the `compress_geonames` command, and eliminates the
        # overhead from using the ORM.  Moreover, copying from a gzipped file
        # reduces disk I/O.
        copy_sql = "COPY %s (geonameid,name,alternates,fclass,fcode,country,cc2,admin1,admin2,admin3,admin4,population,elevation,topo,timezone,moddate,point) FROM STDIN;" % db_table
        copy_cmd = 'gzcat %(gz_file)s | psql %(db_opts)s -c "%(copy_sql)s"'
        copy_args = {'gz_file' : os.path.join(GEONAMES_DATA, 'allCountries.gz'),
                     'db_opts' : db_opts,
                     'copy_sql' : copy_sql
                     }

        # Printing the copy command and executing it.
        if not options['no_geonames']:
            fromfile_args['sql_file'] = os.path.join(GEONAMES_DATA, 'drop_geoname_indexes.sql')
            print(fromfile_cmd % fromfile_args)
            os.system(fromfile_cmd % fromfile_args)
            print(copy_cmd % copy_args)
            os.system(copy_cmd % copy_args)
            fromfile_args['sql_file'] = os.path.join(GEONAMES_DATA, 'create_geoname_indexes.sql')
            print(fromfile_cmd % fromfile_args)
            os.system(fromfile_cmd % fromfile_args)
            print('Finished PostgreSQL `COPY` from Geonames all countries data file.')

        ### COPY'ing into the Geonames alternate table ###

        db_table = Alternate._meta.db_table
        copy_sql = "COPY %s (alternateid,geoname_id,isolanguage,variant,preferred,short) FROM STDIN;" % db_table
        copy_cmd = 'gzcat %(gz_file)s | psql %(db_opts)s -c "%(copy_sql)s"'
        copy_args = {'gz_file' : os.path.join(GEONAMES_DATA, 'alternateNames.gz'),
                     'db_opts' : get_cmd_options(settings.DATABASE_NAME),
                     'copy_sql' : copy_sql
                     } 

        if not options['no_alternates']:
            fromfile_args['sql_file'] = os.path.join(GEONAMES_DATA, 'drop_alternate_indexes.sql')
            print(fromfile_cmd % fromfile_args)
            os.system(fromfile_cmd % fromfile_args)
            print(copy_cmd % copy_args)
            os.system(copy_cmd % copy_args)
            print('Finished PostgreSQL `COPY` from Geonames alternate names data file.')
            fromfile_args['sql_file'] = os.path.join(GEONAMES_DATA, 'create_alternate_indexes.sql')
            print(fromfile_cmd % fromfile_args)
            os.system(fromfile_cmd % fromfile_args)

        # Done
        if options['time']: print('\nCompleted in %s' % (datetime.datetime.now() - start_time))
