from typing_extensions import Required
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from ..models import User, MemberShip, SubscriptionHistory

class MemberShipSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether the membership is currently active"
    )
    type = serializers.CharField(
        required=False,
        help_text="Type of membership (e.g., premium, basic)"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="When the membership started"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="When the membership ends"
    )
    auto_renew = serializers.BooleanField(
        default=False,
        help_text="Whether the membership will auto-renew"
    )
    last_payment_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="ID of the last payment for this membership"
    )

class SubscriptionHistorySerializer(serializers.Serializer):
    subscription_id = serializers.CharField(
        required=False,
        help_text="Unique identifier for the subscription"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="When the subscription started"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="When the subscription ended"
    )
    payment_amount = serializers.FloatField(
        required=False,
        min_value=0,
        help_text="Amount paid for the subscription"
    )
    currency = serializers.CharField(
        required=False,
        help_text="Currency code for the payment (e.g., USD, EUR)"
    )
    payment_date = serializers.DateTimeField(
        required=False,
        help_text="When the payment was made"
    )

class UserSerializer(serializers.Serializer):
    id = serializers.CharField(
        read_only=True,
        help_text="Unique identifier for the user"
    )
    username = serializers.CharField(
        max_length=150,
        help_text="User's unique username"
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="User's password (write-only)"
    )
    created_at = serializers.DateTimeField(
        read_only=True,
        help_text="When the user account was created"
    )
    updated_at = serializers.DateTimeField(
        read_only=True,
        help_text="When the user account was last updated"
    )
    member_ship = MemberShipSerializer(
        required=False,
        allow_null=True,
        help_text="User's membership information"
    )
    history = SubscriptionHistorySerializer(
        many=True,
        required=False,
        help_text="List of user's subscription history"
    )
    refresh_token = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        read_only=True,
        help_text="Refresh token for authentication"
    )

    def validate_username(self, value):
        """
        Custom validation for username
        """
        # 在MongoEngine中，使用count() > 0来检查文档是否存在
        if User.objects(username=value).count() > 0:
            raise serializers.ValidationError("Username already exists")
        return value

    def create(self, validated_data):
        """
        Create user with nested membership and history
        """
        member_ship_data = validated_data.pop('member_ship', None)
        history_data = validated_data.pop('history', [])
        
        # Hash password if it exists
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        
        user = User(**validated_data)
        
        if member_ship_data:
            user.member_ship = MemberShip(**member_ship_data)
        
        if history_data:
            user.history = [SubscriptionHistory(**h) for h in history_data]
        
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Update user with nested membership and history
        """
        # Update basic fields
        instance.username = validated_data.get('username', instance.username)
        
        if 'password' in validated_data:
            instance.password = make_password(validated_data['password'])
        
        # Update membership
        if 'member_ship' in validated_data:
            member_ship_data = validated_data['member_ship']
            if not instance.member_ship:
                instance.member_ship = MemberShip(**member_ship_data)
            else:
                for key, value in member_ship_data.items():
                    setattr(instance.member_ship, key, value)
        
        # Update history (complete replacement)
        if 'history' in validated_data:
            instance.history = [
                SubscriptionHistory(**h) 
                for h in validated_data['history']
            ]
        
        instance.save()
        return instance