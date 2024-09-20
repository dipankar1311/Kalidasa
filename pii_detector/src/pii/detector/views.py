import logging
import timeit


from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User


from pii.detector.logic import process_text

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')


class ProcessText(APIView):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    """
    {
        "text": "I hold a MasterCard with number 4111-1111-1111-1111, expiring on 12/23, with CVV 456."
    }
    """
    def get(self, request, format=None):
        return Response({
        "text": "I hold a MasterCard with number 4111-1111-1111-1111, expiring on 12/23, with CVV 456."
    })

    """
    View to process text.
    """
    def post(self, request, format=None):
        start = timeit.default_timer()
        self.logger.warn(request.data)
        data = process_text(request.data["text"])
        self.logger.warn(data)
        stop = timeit.default_timer()
        data["time"] = round(stop - start, 2)
        return Response(data)


class ListUsers(APIView):
    """
    View to list all users in the system.
    - doc
    """
    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)
