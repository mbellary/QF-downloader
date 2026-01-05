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
            item = {
                "pk": self._av_s(pk),
                "sk": self._av_s(sk),
                "provider": self._av_s(provider),
                "pair": self._av_s(pair),
                "date": self._av_s(date),
                "s3_key": self._av_s(s3_key),
                "state": self._av_s("PENDING"),
            }
            await dynamo.put_item(TableName=self.table_name, Item=item)

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

            while True:
                resp = await dynamo.query(**query_kwargs)
                for item in resp.get("Items", []):
                    if "s3_key" in item:
                        results.append(self._unwrap_s(item["s3_key"]))

                lek = resp.get("LastEvaluatedKey")
                if not lek:
                    break
                query_kwargs = query_kwargs | {"ExclusiveStartKey": lek}

        results = sorted(results)
        logger.info("Queried index for %s/%s -> %d keys", provider, pair, len(results))
        return results
