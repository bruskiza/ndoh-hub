from rest_framework import serializers

from .fields import PhoneNumberField
from .models import Change


class OneFieldRequiredValidator:
    def __init__(self, fields):
        self.fields = fields

    def set_context(self, serializer):
        self.is_create = getattr(serializer, "instance", None) is None

    def __call__(self, data):
        if self.is_create:

            for field in self.fields:
                if data.get(field):
                    return

            raise serializers.ValidationError(
                "One of these fields must be populated: %s" % (", ".join(self.fields))
            )


class ChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Change
        read_only_fields = (
            "validated",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        )
        fields = (
            "id",
            "action",
            "registrant_id",
            "data",
            "validated",
            "source",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )


class AdminOptoutSerializer(serializers.Serializer):
    registrant_id = serializers.UUIDField(allow_null=False)


class AdminChangeSerializer(serializers.Serializer):
    registrant_id = serializers.UUIDField(allow_null=False)
    subscription = serializers.UUIDField(allow_null=False)
    messageset = serializers.CharField(required=False)
    language = serializers.CharField(required=False)

    validators = [OneFieldRequiredValidator(["messageset", "language"])]


class ReceiveWhatsAppEventSerializer(serializers.Serializer):
    class StatusSerializer(serializers.Serializer):
        class ErrorSerializer(serializers.Serializer):
            code = serializers.IntegerField(required=False)
            title = serializers.CharField(required=True)

        id = serializers.CharField(required=True)
        status = serializers.ChoiceField(["failed", "sent", "delivered", "read"])
        errors = serializers.ListField(child=ErrorSerializer(), default=[])

    statuses = serializers.ListField(child=StatusSerializer(), min_length=1)

    def to_internal_value(self, data):
        if "statuses" in data:
            statuses = []
            for status in data["statuses"]:
                if status["status"] == "failed":
                    statuses.append(status)

            data["statuses"] = statuses

        return super(ReceiveWhatsAppEventSerializer, self).to_internal_value(data)


class ReceiveEngageMessage(serializers.Serializer):
    # We're only interested in text messages
    type = serializers.ChoiceField(["text"])

    class Vnd(serializers.Serializer):
        class V1(serializers.Serializer):
            class Author(serializers.Serializer):
                # We're only interested in messages sent from Engage UI
                type = serializers.ChoiceField(["OPERATOR"])

            class Chat(serializers.Serializer):
                owner = serializers.CharField(required=True)

            author = Author()
            chat = Chat()
            direction = serializers.ChoiceField(["outbound"])

        v1 = V1()

    _vnd = Vnd()


class ReceiveWhatsAppSystemEventSerializer(serializers.Serializer):
    class EventSerializer(serializers.Serializer):
        type = serializers.CharField(required=True)
        message_id = serializers.CharField(required=True)
        recipient_id = serializers.CharField(required=True)

    events = serializers.ListField(child=EventSerializer(), min_length=1)


class SeedMessageSenderHookSerializer(serializers.Serializer):
    class Hook(serializers.Serializer):
        id = serializers.IntegerField()
        event = serializers.ChoiceField(choices=["whatsapp.failed_contact_check"])
        target = serializers.CharField()

    hook = Hook()

    class Data(serializers.Serializer):
        address = PhoneNumberField(country_code="ZA")

    data = Data()


class SeedMessageSenderFailedMsisdnHookSerializer(serializers.Serializer):
    class Hook(serializers.Serializer):
        id = serializers.IntegerField()
        event = serializers.ChoiceField(choices=["identity.no_address"])
        target = serializers.CharField()

    hook = Hook()

    class Data(serializers.Serializer):
        to_identity = serializers.UUIDField()

    data = Data()
