from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

todays_date = timezone.now().date()

class StaffMemberPagination(PageNumberPagination):
    page_size = 10  # Set the default page size for pagination
    page_size_query_param = 'page_size'
    max_page_size = 100  # Max number of items per page