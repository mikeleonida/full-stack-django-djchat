# Import necessary modules and classes from Django and rest_framework
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

# Import the Server model and its corresponding serializer
from .models import Server
from .schema import server_list_docs
from .serializer import ServerSerializer


# Create a viewset for handling ServerListViewSet operations
class ServerListViewSet(viewsets.ViewSet):
    # Set the initial queryset to retrieve all Server objects
    queryset = Server.objects.all()

    @server_list_docs
    def list(self, request):
        """Retrieves a list of Server objects based on optional query parameters.

        Args:
            request (HttpRequest): The HTTP request containing optional query parameters.

        Returns:
            Response: A Response object containing the serialized data of the retrieved Server objects.

        Raises:
            AuthenticationFailed: If the 'by_user' parameter is set to 'true', but the user is not authenticated.
            ValidationError: If the 'by_serverid' parameter is set and the specified Server ID does not exist.

        Notes:
            This method filters the Server queryset based on the following optional query parameters:
            - 'category': Filters the queryset by Servers with the specified category name.
            - 'qty': Limits the queryset to return only a specified number of Server objects.
            - 'by_user': Filters the queryset to retrieve Servers with a specific member (user) if set to 'true'.
            - 'with_num_members': Annotates the queryset with the number of members in each server if set to 'true'.
            - 'by_serverid': Filters the queryset to retrieve a specific Server by its ID.

        Example:
            To retrieve Servers belonging to a specific category and limit the response to 10 objects:
            ```
            GET /api/servers/?category=gaming&qty=10
            ```

            To retrieve Servers with a specific member (user) and include the number of members in each Server:
            ```
            GET /api/servers/?by_user=true&with_num_members=true
            ```

            To retrieve a specific Server by its ID:
            ```
            GET /api/servers/?by_serverid=123
            ```
        """

        # Retrieve optional query parameters from the request
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members")

        # Filter the queryset by the specified 'category' if it is provided in the request
        if category:
            self.queryset = self.queryset.filter(category__name=category)

        # If 'by_user' parameter is set, filter the queryset to retrieve Servers with a specific member (user)
        if by_user:
            if request.user.is_authenticated:
                user_id = request.user.id
                self.queryset = self.queryset.filter(member=user_id)
            else:
                raise AuthenticationFailed()

        # If 'with_num_members' parameter is set, annotate the queryset with the number of members in each server
        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        # If 'by_serverid' parameter is set, filter the queryset to retrieve a specific Server by its ID
        if by_serverid:
            if not request.user.is_authenticated:
                raise AuthenticationFailed()

            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                # Raise a validation error if the Server with the specified ID doesn't exist
                if not self.queryset.exists():
                    raise ValidationError(detail=f"Server with id {by_serverid} not found")
            except ValueError:
                raise ValidationError(detail="Server value error")

        # If 'qty' parameter is set, limit the queryset to return only the specified number of Server objects
        if qty:
            self.queryset = self.queryset[: int(qty)]

        # Serialize the filtered queryset using the ServerSerializer, passing 'num_members' context if specified
        serializer = ServerSerializer(self.queryset, many=True, context={"num_members": with_num_members})

        # Return the serialized data as a response
        return Response(serializer.data)
