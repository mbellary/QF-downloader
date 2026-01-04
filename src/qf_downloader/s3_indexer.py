from .aws_clients import get_aboto3_client
from .config import RAW_FILE_INDEX_TABLE
from .logger import get_logger

logger = get_logger("downloader.s3_indexer")


class S3Indexer:
    def __init__(self, table_name: str = RAW_FILE_INDEX_TABLE):
        self.table_name = table_name

    @staticmethod
    def _av_s(value: str) -> dict[str, str]:
        # DynamoDB AttributeValue for a string.
        return {"S": value}

    @staticmethod
    def _unwrap_s(av: object) -> str:
        # Extract a string from a DynamoDB AttributeValue.
        if isinstance(av, dict) and "S" in av:
            return str(av["S"])
        # Fallback for unexpected shapes.
        return str(av)

    async def index_file(self, provider: str, pair: str, date: str, s3_key: str) -> None:
        pk = f"{pair}#{provider}"
        sk = f"{date}#{s3_key}"

        async with await get_aboto3_client("dynamodb") as dynamo:
            table = await dynamo.Table(self.table)
            item = {
                "pk": pk,
                "sk": sk,
                "provider": provider,
                "pair": pair,
                "date": date,
                "s3_key": s3_key,
                "state": "PENDING",
            }
            await table.put_item(Item=item)

        logger.info(f"Indexed raw file: pk={pk}, sk={sk}")

    async def query_keys(
        self, provider: str, pair: str, start_date: str, end_date: str
    ) -> list[str]:
        """
        Query DynamoDB for s3_keys in date range (inclusive).
        start_date, end_date format: YYYYMMDD
        Returns sorted list of s3_key strings.
        """
        pk = f"{pair}#{provider}"
        start_sk = f"{start_date}#"
        end_sk = f"{end_date}#~"  # tilde ensures inclusive upper bound

        results: list[str] = []
        async with await get_aboto3_client("dynamodb") as dynamo:
            query_kwargs = {
                "TableName": self.table_name,
                "KeyConditionExpression": "pk = :pk AND sk BETWEEN :start AND :end",
                "ExpressionAttributeValues": {
                    ":pk": self._av_s(pk),
                    ":start": self._av_s(start_sk),
                    ":end": self._av_s(end_sk),
                },
                "Limit": 1000,
            }

            # DynamoDB query paginated
            resp = await table.query(
                KeyConditionExpression="pk = :pk AND sk BETWEEN :start AND :end",
                ExpressionAttributeValues={":pk": pk, ":start": start_sk, ":end": end_sk},
                Limit=1000,
            )
            items = resp.get("Items", [])
            while items:
                for it in items:
                    results.append(it["s3_key"])
                # handle pagination
                if "LastEvaluatedKey" in resp:
                    resp = await table.query(
                        KeyConditionExpression="pk = :pk AND sk BETWEEN :start AND :end",
                        ExpressionAttributeValues={":pk": pk, ":start": start_sk, ":end": end_sk},
                        ExclusiveStartKey=resp["LastEvaluatedKey"],
                        Limit=1000,
                    )
                    items = resp.get("Items", [])
                else:
                    break

                resp = await dynamo.query(**(query_kwargs | {"ExclusiveStartKey": lek}))

        results = sorted(results)
        logger.info("Queried index for %s/%s -> %d keys", provider, pair, len(results))
        return results
