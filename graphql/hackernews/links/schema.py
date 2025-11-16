import graphene
from graphene_django import DjangoObjectType

from .models import Link, Vote
from users.schema import UserType
from graphql import GraphQLError
from django.db.models import Q


class LinkType(DjangoObjectType):
    class Meta:
        model = Link

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote


class Query(graphene.ObjectType):
    links = graphene.List(
        LinkType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
    )
    votes = graphene.List(VoteType)

    def resolve_links(self, info, search=None, first=None, skip=None, **kwargs):
        qs = Link.objects.all()

        # The value sent with the search parameter will be in the args variable
        if search:
            filter = (
                Q(url__icontains=search) |
                Q(description__icontains=search)
            )
            qs = qs.filter(filter)
        
        if skip:
            qs = qs[skip:]

        if first:
            qs = qs[:first]

        return qs
    
    def resolve_votes(self, info, **kwargs):
        return Vote.objects.all()
    
# Define mutation classs
class createLink(graphene.Mutation):
    # define the output (data that server returns to the client)
    id = graphene.Int()
    url = graphene.String()
    description = graphene.String()
    posted_by = graphene.Field(UserType)

    # defines the data you can send to the server
    class Arguments:
        url = graphene.String()
        description = graphene.String()

    # mutate method to handle data sent by the user, creates link in database
    def mutate(self, info, url, description):
        user = info.context.user or None

        link = Link(
                    url=url, 
                    description=description,
                    posted_by=user,
                )
        link.save()

        return createLink(
            id=link.id,
            url=link.url,
            description=link.description,
            posted_by=link.posted_by,
        )


class createVote(graphene.Mutation):
    user = graphene.Field(UserType)
    link = graphene.Field(LinkType)

    class Arguments:
        link_id = graphene.Int()

    def mutate(self, info, link_id):
        user = info.context.user

        if user.is_anonymous:
            raise GraphQLError('You must be logged to vote!')
        
        link = Link.objects.filter(id=link_id).first()
        if not link:
            raise Exception("Invalid Link!")
        
        Vote.objects.create(
            user=user,
            link=link
        )

        return createVote(user=user, link=link)
    
# creates a mutation class with a field to be resolved
class Mutation(graphene.ObjectType):
    create_link = createLink.Field()
    create_vote = createVote.Field()
    
