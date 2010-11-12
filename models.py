from django.contrib.gis.db import models

class BigIntegerField(models.PositiveIntegerField):
    def db_type(self):
        return 'bigint'

### Geonames.org Models ###

class Admin1Code(models.Model):
    code = models.CharField(max_length=6)
    name = models.CharField(max_length=58)
    
    objects = models.GeoManager()

    def __unicode__(self):
        return u': '.join([self.code, self.name])

class Admin2Code(models.Model):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=46)
    
    objects = models.GeoManager()

    def __unicode__(self):
        return u': '.join([self.code, self.name])
    
class TimeZone(models.Model):
    tzid = models.CharField(max_length=30)
    gmt_offset = models.FloatField()
    dst_offset = models.FloatField()
    
    objects = models.GeoManager()
    
    def __unicode__(self):
        return self.tzid

class Geoname(models.Model):
    geonameid = models.PositiveIntegerField(primary_key=True, unique=True)
    name = models.CharField(max_length=154, db_index=True)
    alternates = models.TextField(blank=True)
    fclass = models.CharField(max_length=1, db_index=True)
    fcode = models.CharField(max_length=5, db_index=True)
    country = models.CharField(max_length=2, blank=True, db_index=True)
    cc2 = models.CharField('Alternate Country Code', max_length=32, blank=True)
    admin1 = models.CharField(max_length=6, blank=True, db_index=True)
    admin2 = models.CharField(max_length=63, blank=True, db_index=True)
    admin3 = models.CharField(max_length=10, blank=True, db_index=True)
    admin4 = models.CharField(max_length=8, blank=True, db_index=True)
    population = BigIntegerField(db_index=True)
    elevation = models.IntegerField(db_index=True)
    topo = models.IntegerField(db_index=True)
    timezone = models.CharField(max_length=30, blank=True)
    moddate = models.DateField('Date of Last Modification')
    point = models.PointField(null=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

class Alternate(models.Model):
    alternateid = models.PositiveIntegerField(primary_key=True, unique=True)
    geoname = models.ForeignKey(Geoname)
    isolanguage = models.CharField(max_length=7)
    variant = models.CharField(max_length=222, db_index=True)
    preferred = models.BooleanField()
    short = models.BooleanField()

    objects = models.GeoManager()

    def __unicode__(self):
        return self.geoname.name
