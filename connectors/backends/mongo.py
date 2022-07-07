#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
from datetime import datetime
from collections.abc import Iterable

from bson import Decimal128
from motor.motor_asyncio import AsyncIOMotorClient
from connectors.elastic import ElasticServer


class MongoConnector:
    """MongoDB"""

    def __init__(self, definition):
        self.definition = definition
        self.config = definition.configuration
        self.host = self.config.get("host", "mongodb://127.0.0.1:27021")
        self.database = self.config["database"]
        self.collection = self.config["collection"]
        self.client = AsyncIOMotorClient(
            self.host,
            directConnection=True,
            connectTimeoutMS=60,
            socketTimeoutMS=60,
        )
        self.db = self.client[self.database]

    async def ping(self):
        await self.client.admin.command("ping")

    # XXX That's a lot of work...
    def serialize(self, doc):
        def _serialize(value):
            if isinstance(value, (list, tuple)):
                value = [_serialize(item) for item in value]
            elif isinstance(value, dict):
                for key, svalue in value.items():
                    value[key] = _serialize(svalue)
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal128):
                value = value.to_decimal()
            return value

        for key, value in doc.items():
            doc[key] = _serialize(value)

        return doc

    async def get_docs(self):
        async for doc in self.db[self.collection].find():
            yield self.serialize(doc)