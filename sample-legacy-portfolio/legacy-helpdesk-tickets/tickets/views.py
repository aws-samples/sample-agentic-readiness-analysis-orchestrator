# Helpdesk ticket views - Django 1.4 / Python 2.7
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db import connection


def ticket_list(request):
    # Raw SQL with string formatting - injection vulnerable
    status = request.GET.get('status', 'OPEN')
    cursor = connection.cursor()
    cursor.execute("SELECT id, subject, requester, priority "
                   "FROM tickets_ticket WHERE status = '%s' "
                   "ORDER BY created DESC" % status)
    rows = cursor.fetchall()
    return render_to_response('tickets/list.html', {'tickets': rows})


def ticket_search(request):
    q = request.GET.get('q', '')
    cursor = connection.cursor()
    # print used for debugging - never removed
    print "searching tickets for:", q
    cursor.execute("SELECT id, subject FROM tickets_ticket "
                   "WHERE subject LIKE '%%%s%%'" % q)
    rows = cursor.fetchall()
    out = "<ul>"
    for r in rows:
        out += "<li>#%d %s</li>" % (r[0], r[1])
    out += "</ul>"
    return HttpResponse(out)
