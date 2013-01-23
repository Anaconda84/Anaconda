# -*- coding: utf-8 -*-
# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse
from VideoApp.models import VideoBaza
from VideoApp.utils import *

#import os

def video(request):
    list = VideoBaza.objects.all()
    return render_to_response('base.html', {'list':list})

def version(request):
    return HttpResponse("0.9")

def seeders(request, torrent):
    resp = get_seeders(request, torrent)
    out = ''
    i = 0
    for ip in resp:
      if i == 0:
          out = ip
      else:
          out = out+','+ip
      i = i + 1

    return HttpResponse(out)

                                                        