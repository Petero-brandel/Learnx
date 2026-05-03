import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from emails.tasks import send_verification_email_task
from .serializers import RegisterSerializer, UserSerializer, GoogleAuthSerializer

User = get_user_model()

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')


class RegisterView(generics.CreateAPIView):
    """Standard email/password registration."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate verification token
        user.verification_token = get_random_string(64)
        user.save(update_fields=['verification_token'])

        # Send verification email
        try:
            send_verification_email_task(user.id)
        except Exception as e:
            # Log the error in production, but continue the flow
            print(f"Failed to send verification email: {str(e)}")

        # Return a success message instead of JWT tokens.
        # User must verify email before logging in.
        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """Returns the currently authenticated user's profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class GoogleAuthView(APIView):
    """
    Receives a Google id_token (credential) from the frontend,
    verifies it, creates a user if needed, and returns JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credential = serializer.validated_data.get('credential')
        access_token = serializer.validated_data.get('access_token')

        try:
            if access_token:
                # Verify access_token using Google UserInfo endpoint
                response = requests.get(f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={access_token}")
                if not response.ok:
                    return Response({'error': 'Invalid Google access token'}, status=status.HTTP_400_BAD_REQUEST)
                idinfo = response.json()
            else:
                # Verify the Google id_token (credential)
                idinfo = id_token.verify_oauth2_token(
                    credential,
                    google_requests.Request(),
                    GOOGLE_CLIENT_ID,
                )

            email = idinfo.get('email')
            if not email:
                return Response({'error': 'Google token missing email.'}, status=status.HTTP_400_BAD_REQUEST)

            full_name = idinfo.get('name', '')
            profile_photo = idinfo.get('picture', '')

            # Get or create the user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'profile_photo': profile_photo,
                    'is_email_verified': True, # Google accounts are already verified
                }
            )

            # If user already exists, update their profile photo from Google
            if not created and profile_photo:
                user.profile_photo = profile_photo
                user.save(update_fields=['profile_photo'])

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'created': created,
            })

        except ValueError as e:
            return Response({'error': f'Invalid Google token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """Verifies a user's email using a token."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(verification_token=token)
            user.is_email_verified = True
            user.verification_token = None
            user.save(update_fields=['is_email_verified', 'verification_token'])
            return Response({'message': 'Email verified successfully. You can now log in.'})
        except User.DoesNotExist:
            return Response({'error': 'Invalid or expired verification token.'}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that enforces email verification."""
    serializer_class = CustomTokenObtainPairSerializer

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from emails.tasks import send_password_reset_email_task
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer

class PasswordResetRequestView(APIView):
    """Requests a password reset email."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Send the email
            try:
                send_password_reset_email_task(user.id, uidb64, token)
            except Exception as e:
                print(f"Failed to send password reset email: {str(e)}")
                
        except User.DoesNotExist:
            # Silently ignore to prevent email enumeration
            pass
            
        return Response({'message': 'If that email address is in our database, we will send you an email to reset your password.'})

class PasswordResetConfirmView(APIView):
    """Confirms the password reset with a token."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            
        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password has been reset successfully. You can now log in.'})
        else:
            return Response({'error': 'Invalid or expired password reset link.'}, status=status.HTTP_400_BAD_REQUEST)
