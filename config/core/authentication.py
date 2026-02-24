"""
JWT authentication that attaches request.organization from the authenticated user.

This keeps organization resolution in the DRF authentication layer for JWT APIs.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTAuthenticationWithOrganization(JWTAuthentication):

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result
        organization = getattr(user, "organization", None)
        if organization is None:
            raise AuthenticationFailed(
                detail="User has no organization assigned. Assign one in Django admin."
            )

        request.organization = organization
        return (user, validated_token)
