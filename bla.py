import asyncio

from aiohttp import ClientSession

from aiopulse import Aiopulse, InputSchemaBase, RequestBuildMapping, TransformerBase
from aiopulse.data_types import SerializableURL
from aiopulse.response import simple_json_processor


async def main():
    # Create an input schema for users to send requests to https://<servicename>.jsontest.com
    class JsonTest(InputSchemaBase):
        service_name: str

    # Create transformers for modifying/extending the user input
    class SetJsonTestUrl(TransformerBase):
        def transform_input(self, input_data: dict):
            service_name = input_data["service_name"]
            url = SerializableURL(f"http://{service_name}.jsontest.com")
            input_data["url"] = url
            return input_data

    class AddHelloWorldHeader(TransformerBase):
        def transform_input(self, input_data: dict):
            return input_data | {"headers": {"x-hello": "world"}}

    class AddGetMethod(TransformerBase):
        def transform_input(self, input_data: dict):
            return input_data | {"method": "GET"}

    # Initialize the client
    client = Aiopulse()

    # Create and register new mappings

    def is_header_request(data: dict):
        return "service_name" in data.keys() and data["service_name"] == "headers"

    def is_date_request(data: dict):
        return "service_name" in data.keys() and data["service_name"] == "date"

    header_request = RequestBuildMapping(
        title="Json Test (Hello World)",
        description="Send a request to headers.jsontest.com with a hello world header",
        input_schema=JsonTest,
        transformers=[SetJsonTestUrl, AddGetMethod, AddHelloWorldHeader],
        response_processor=simple_json_processor,
        is_match=is_header_request,
    )

    date_request = RequestBuildMapping(
        title="Json Test (Date)",
        description="Send a request to date.jsontest.com",
        input_schema=JsonTest,
        transformers=[SetJsonTestUrl, AddGetMethod],
        response_processor=simple_json_processor,
        is_match=is_date_request,
    )

    client.register_mapping(header_request)
    client.register_mapping(date_request)

    # Populate the queue with requests

    await client.build_and_add_to_queue({"service_name": "headers", "description": "display headers"})
    await client.build_and_add_to_queue({"service_name": "date", "description": "display date"})

    # Process the queue and display results

    async with ClientSession() as session:
        results = await client.process_queue(session, batch_size=2)

    print(results)


if __name__ == "__main__":
    asyncio.run(main())
