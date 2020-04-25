import graphene
from django.contrib.auth import get_user_model
from graphene import relay
from graphene_django import DjangoConnectionField
from graphene_django.filter import DjangoFilterConnectionField
from rest_framework_guardian.filters import ObjectPermissionsFilter

from whoweb.contrib.graphene_django.types import GuardedObjectType, ObscureIdNode
from whoweb.contrib.rest_framework.permissions import (
    IsSuperUser,
    ObjectPermissions,
    ObjectPassesTest,
)
from whoweb.users.models import UserProfile, Group, Seat, DeveloperKey

User = get_user_model()


def member_of_network(viewer: User, user: User):
    return not set(viewer.users_group.all().values_list("pk", flat=True)).isdisjoint(
        user.users_group.all().values_list("pk", flat=True)
    )


class UserNode(GuardedObjectType):
    class Meta:
        model = User
        fields = ("username",)
        filter_fields = {"username": ["exact", "icontains", "istartswith"]}
        interfaces = (relay.Node,)
        permission_classes = [
            ObjectPassesTest(member_of_network) | IsSuperUser | ObjectPermissions
        ]
        filter_backends = (ObjectPermissionsFilter,)


class UserProfileNode(GuardedObjectType):
    class Meta:
        model = UserProfile
        filter_fields = ["user"]
        interfaces = (ObscureIdNode,)
        permission_classes = [IsSuperUser | ObjectPermissions]
        filter_backends = (ObjectPermissionsFilter,)


class NetworkNode(GuardedObjectType):
    class Meta:
        model = Group
        filter_fields = {
            "slug": ["exact", "icontains", "istartswith"],
            "name": ["exact", "icontains", "istartswith"],
        }
        interfaces = (ObscureIdNode,)
        permission_classes = [IsSuperUser | ObjectPermissions]
        filter_backends = (ObjectPermissionsFilter,)


class SeatNode(GuardedObjectType):
    class Meta:
        model = Seat
        filter_fields = {
            "display_name": ["exact", "icontains", "istartswith"],
            "user": ["exact"],
        }
        interfaces = (ObscureIdNode,)
        permission_classes = [IsSuperUser | ObjectPermissions]
        filter_backends = (ObjectPermissionsFilter,)


class DeveloperKeyNode(GuardedObjectType):
    class Meta:
        model = DeveloperKey
        fields = ("key", "secret", "test_key", "group", "created", "created_by")
        interfaces = (ObscureIdNode,)
        permission_classes = [IsSuperUser | ObjectPermissions]
        filter_backends = (ObjectPermissionsFilter,)


class Query(graphene.ObjectType):
    user = relay.Node.Field(UserProfileNode)
    users = DjangoFilterConnectionField(UserProfileNode)
    networks = DjangoFilterConnectionField(NetworkNode)
    seats = DjangoFilterConnectionField(SeatNode)
    developer_keys = DjangoConnectionField(DeveloperKeyNode)
