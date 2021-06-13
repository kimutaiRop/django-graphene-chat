import channels
import channels_graphql_ws
import graphene
from django.utils.timezone import now
from graphene_django.filter import DjangoFilterConnectionField
from graphql_auth import mutations
from graphql_auth.schema import MeQuery

from chat.models import Chat, Message
from chat.serializer import ChatType, ChatFilter, MessageType, MessageFilter


class AuthMutation(graphene.ObjectType):
    register = mutations.Register.Field()
    verify_account = mutations.VerifyAccount.Field()
    resend_activation_email = mutations.ResendActivationEmail.Field()
    send_password_reset_email = mutations.SendPasswordResetEmail.Field()
    password_reset = mutations.PasswordReset.Field()
    password_set = mutations.PasswordSet.Field()  # For passwordless registration
    password_change = mutations.PasswordChange.Field()
    update_account = mutations.UpdateAccount.Field()
    archive_account = mutations.ArchiveAccount.Field()
    delete_account = mutations.DeleteAccount.Field()
    send_secondary_email_activation = mutations.SendSecondaryEmailActivation.Field()
    verify_secondary_email = mutations.VerifySecondaryEmail.Field()
    swap_emails = mutations.SwapEmails.Field()
    remove_secondary_email = mutations.RemoveSecondaryEmail.Field()

    # django-graphql-jwt inheritances
    token_auth = mutations.ObtainJSONWebToken.Field()
    verify_token = mutations.VerifyToken.Field()
    refresh_token = mutations.RefreshToken.Field()
    revoke_token = mutations.RevokeToken.Field()


class Query(MeQuery, graphene.ObjectType):
    chats = DjangoFilterConnectionField(ChatType, filterset_class=ChatFilter)
    chat = graphene.Field(ChatType, id=graphene.ID())
    messages = DjangoFilterConnectionField(
        MessageType,
        filterset_class=MessageFilter, id=graphene.ID())

    @staticmethod
    def resolve_chats(cls, info, **kwargs):
        user = info.context.user
        return Chat.objects.prefetch_related("messages", "participants").filter(participants=user)

    @staticmethod
    def resolve_chat(cls, info, id, **kwargs):
        user = info.context.user
        return Chat.objects.prefetch_related("participants").get(participants=user, id=id)

    @staticmethod
    def resolve_messages(cls, info, id, **kwargs):
        user = info.context.user
        chat = Chat.objects.prefetch_related("messages", "participants").get(participants=user, id=id)
        return chat.messages.all()


class CreateChat(graphene.Mutation):
    chat = graphene.Field(ChatType)
    error = graphene.String()

    class Arguments:
        emails = graphene.String(required=True)
        group = graphene.Boolean()

    @classmethod
    def mutate(cls, info, emails, group):
        emails = emails.split(",")
        if not group:
            if len(emails) > 2:
                return CreateChat(error="you cannot have more then two participants if this is not a group")
            else:
                # get user and add to chat participants
                pass
        else:
            # create chat and add the paerticipants
            pass


class SendMessage(graphene.Mutation):
    message = graphene.Field(MessageType)

    class Arguments:
        message = graphene.String(required=True)
        chat_id = graphene.Int(required=True)

    @classmethod
    def mutate(cls, info, message, chat_id):
        user = info.context.user
        chat = Chat.objects.prefetch_related("participants").get(participants=user, id=chat_id)
        message = Message.objects.create(
            sender=user,
            text=message,
            created=now()
        )
        chat.messages.add(message)
        users = [usr for usr in chat.participants.all() if usr != user]
        for usr in users:
            OnNewMessage.broadcast(payload=message, group=usr.username)
        return SendMessage(message=message)


class OnNewMessage(channels_graphql_ws.Subscription):
    message = graphene.Field(MessageType)

    class Arguments:
        chatroom = graphene.String()

    def subscribe(cls, info, chatroom=None):
        return [chatroom] if chatroom is not None else None

    def publish(self, info, chatroom=None):
        return OnNewMessage(
            message=self
        )


class Mutations(AuthMutation, graphene.ObjectType):
    send_message = SendMessage.Field()


class Subscription(graphene.ObjectType):
    on_new_message = OnNewMessage.Field()


schema = graphene.Schema(query=Query, mutation=Mutations, subscription=Subscription)


class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    schema = schema

    async def on_connect(self, payload):
        self.scope['user'] = await channels.auth.get_user(self.scope)
