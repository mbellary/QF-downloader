import aioboto3
from .config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from .logger import get_logger
from .aws_clients import get_aboto3_client
from .config import RAW_FILE_INDEX_TABLE

logger = get_logger("downloader.s3_indexer")


class S3Indexer:
    def __init__(self, table_name: str = RAW_FILE_INDEX_TABLE):
        self.table = table_name
        # self._session = aioboto3.Session(
        #     aws_access_key_id=AWS_ACCESS_KEY_ID,
        #     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        #     region_name=AWS_REGION,
        # )

    async def index_file(self, provider: str, pair: str, date: str, s3_key: str):
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
                "state": "PENDING"
            }
            await table.put_item(Item=item)

        logger.info(f"Indexed raw file: pk={pk}, sk={sk}")

    async def query_keys(self, provider: str, pair: str, start_date: str, end_date: str):
        """
        Query DynamoDB for s3_keys in date range (inclusive).
        start_date, end_date format: YYYYMMDD
        Returns sorted list of s3_key strings.
        """
        pk = f"{pair}#{provider}"
        start_sk = f"{start_date}#"
        end_sk = f"{end_date}#~"  # tilde ensures inclusive upper bound

        results = []
        async with await get_aboto3_client("dynamodb") as dynamo:
            table = await dynamo.Table(self.table)

            # DynamoDB query paginated
            resp = await table.query(
                KeyConditionExpression="pk = :pk AND sk BETWEEN :start AND :end",
                ExpressionAttributeValues={":pk": pk, ":start": start_sk, ":end": end_sk},
                Limit=1000
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
                        Limit=1000
                    )
                    items = resp.get("Items", [])
                else:
                    break

        results = sorted(results)
        logger.info("Queried index for %s/%s -> %d keys", provider, pair, len(results))
        return results
