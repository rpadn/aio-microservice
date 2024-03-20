from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator

import strawberry

from aio_microservice import Service, ServiceSettings
from aio_microservice.graphql import GraphqlContext, GraphqlExtension


async def test_graphql_test_client_query() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        async def test(self) -> str:
            return "TEST RESPONSE"

    class TestService(Service[ServiceSettings], GraphqlExtension):
        __graphql_schema__ = strawberry.Schema(query=Query)

    service = TestService()
    query = "query { test }"
    response = await service.graphql.schema.execute(query)
    assert response.errors is None
    assert response.data == {"test": "TEST RESPONSE"}


async def test_graphql_test_client_query_with_context() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        async def test(
            self,
            info: strawberry.types.Info[GraphqlContext[TestService], None],
        ) -> str:
            return info.context.service.response

    class TestService(Service[ServiceSettings], GraphqlExtension):
        __graphql_schema__ = strawberry.Schema(query=Query)

        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.response = "TEST RESPONSE"

    service = TestService()
    query = "query { test }"
    response = await service.graphql.schema.execute(query)

    assert response.errors is None
    assert response.data == {"test": "TEST RESPONSE"}


async def test_graphql_test_client_subscription() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        async def dummy(self) -> bool:
            return True

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def test(self, target: int = 100) -> AsyncGenerator[int, None]:
            for i in range(target):
                yield i

    class TestService(Service[ServiceSettings], GraphqlExtension):
        __graphql_schema__ = strawberry.Schema(query=Query, subscription=Subscription)

    service = TestService()
    query = "subscription { test(target: 3) }"
    subscription = await service.graphql.schema.subscribe(query)

    assert isinstance(subscription, AsyncIterator)
    responses = [x async for x in subscription]
    assert len(responses) == 3
    assert responses[0].data == {"test": 0}
    assert responses[1].data == {"test": 1}
    assert responses[2].data == {"test": 2}


async def test_graphql_test_client_subscription_with_context() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        async def dummy(self) -> bool:
            return True

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def test(
            self,
            info: strawberry.types.Info[GraphqlContext[TestService], None],
            target: int = 100,
        ) -> AsyncGenerator[str, None]:
            for i in range(target):
                yield f"{info.context.service.response_prefix}-{i}"  # type: ignore

    class TestService(Service[ServiceSettings], GraphqlExtension):
        __graphql_schema__ = strawberry.Schema(query=Query, subscription=Subscription)

        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.response_prefix = "TEST"

    service = TestService()
    query = "subscription { test(target: 3) }"
    subscription = await service.graphql.schema.subscribe(query)

    assert isinstance(subscription, AsyncIterator)
    responses = [x async for x in subscription]
    assert len(responses) == 3
    assert responses[0].data == {"test": "TEST-0"}
    assert responses[1].data == {"test": "TEST-1"}
    assert responses[2].data == {"test": "TEST-2"}
