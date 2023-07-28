# Import necessary modules and classes from Django and rest_framework
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

# Import the Server model and its corresponding serializer
from .models import Server
from .serializer import ServerSerializer


# Create a viewset for handling ServerListViewSet operations
class ServerListViewSet(viewsets.ViewSet):
    # Set the initial queryset to retrieve all Server objects
    queryset = Server.objects.all()

    # Define the 'list' method to handle HTTP GET requests for retrieving Server data
    def list(self, request):
        # Retrieve optional query parameters from the request
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members")

        # Check if the request is attempting to filter by user but the user is not authenticated
        if by_user and not request.user.is_authenticated:
            raise AuthenticationFailed()

        # Filter the queryset by the specified 'category' if it is provided in the request
        if category:
            self.queryset = self.queryset.filter(category__name=category)

        # If 'by_user' parameter is set, filter the queryset to retrieve Servers with a specific member (user)
        if by_user:
            user_id = request.user.id
            self.queryset = self.queryset.filter(member=user_id)

        # If 'with_num_members' parameter is set, annotate the queryset with the number of members in each server
        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        # If 'qty' parameter is set, limit the queryset to return only the specified number of Server objects
        if qty:
            self.queryset = self.queryset[: int(qty)]

        # If 'by_serverid' parameter is set, filter the queryset to retrieve a specific Server by its ID
        if by_serverid:
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                # Raise a validation error if the Server with the specified ID doesn't exist
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server with id {by_serverid} not found")
            except ValueError:
                raise ValidationError(detail="Server value error")

        # Serialize the filtered queryset using the ServerSerializer, passing 'num_members' context if specified
        serializer = ServerSerializer(self.queryset, many=True, context={"num_members": with_num_members})

        # Return the serialized data as a response
        return Response(serializer.data)
