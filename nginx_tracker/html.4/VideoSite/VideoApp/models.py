from django.db import models

# Create your models here.
class VideoBaza(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.CharField(max_length=2048, blank=True)
    year = models.CharField(max_length=4, blank=True)
    register = models.CharField(max_length=255, blank=True)
    actors = models.CharField(max_length=2048, blank=True)
    duration = models.CharField(max_length=5, blank=True)
    rating = models.CharField(max_length=1, blank=True)    
    janr = models.CharField(max_length=50, blank=True)
    publication_date = models.CharField(max_length=20)
    poster = models.CharField(max_length=255)
    url = models.URLField()
    torrent = models.CharField(max_length=255)
    
    def __unicode__(self):
	return self.name
