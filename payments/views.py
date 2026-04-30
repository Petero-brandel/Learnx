import json
import uuid
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Payment, Enrollment
from courses.models import Course
from .paystack import initialize_transaction, verify_signature

class CheckoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate a unique reference
        reference = f"LX-{uuid.uuid4().hex[:12].upper()}"
        amount_in_kobo = int(course.price * 100)

        # Initialize transaction with Paystack
        auth_url = initialize_transaction(request.user.email, amount_in_kobo, reference)

        if auth_url:
            # Create a pending payment record
            Payment.objects.create(
                user=request.user,
                course=course,
                amount=course.price,
                reference=reference,
                status='pending'
            )
            return Response({'authorization_url': auth_url})
        
        return Response({'error': 'Failed to initialize payment'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(views.APIView):
    permission_classes = [AllowAny] # Paystack servers don't have our auth tokens

    def post(self, request, *args, **kwargs):
        payload_body = request.body
        signature_header = request.headers.get('x-paystack-signature', '')

        # 1. Verify the signature to prevent spoofing
        if not verify_signature(payload_body, signature_header):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_data = json.loads(payload_body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Handle successful charges
        if event_data.get('event') == 'charge.success':
            data = event_data.get('data', {})
            reference = data.get('reference')
            paystack_id = data.get('id')

            try:
                payment = Payment.objects.get(reference=reference, status='pending')
            except Payment.DoesNotExist:
                # Payment already processed or reference is invalid
                return Response(status=status.HTTP_200_OK)

            # Update Payment status
            payment.status = 'success'
            payment.paystack_id = str(paystack_id)
            payment.save()

            # Auto-enroll the user
            Enrollment.objects.get_or_create(
                user=payment.user,
                course=payment.course
            )

        return Response(status=status.HTTP_200_OK)
