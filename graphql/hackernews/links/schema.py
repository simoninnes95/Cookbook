import graphene
from graphene_django import DjangoObjectType

from .models import Link


class LinkType(DjangoObjectType):
    class Meta:
        model = Link


class Query(graphene.ObjectType):
    links = graphene.List(LinkType)

    def resolve_links(self, info, **kwargs):
        return Link.objects.all()
    
# Define mutation classs
class createLink(graphene.Mutation):
    # define the output (data that server returns to the client)
    id = graphene.Int()
    url = graphene.String()
    description = graphene.String()

    # defines the data you can send to the server
    class Arguments:
        url = graphene.String()
        description = graphene.String()

    # mutate method to handle data sent by the user, creates link in database
    def mutate(self, info, url, description):
        link = Link(url=url, description=description)
        link.save()

        return createLink(
            id=link.id,
            url=link.url,
            description=link.description
        )
    
# creates a mutation class with a field to be resolved
class Mutation(graphene.ObjectType):
    create_link = createLink.Field()