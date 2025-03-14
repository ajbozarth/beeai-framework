import asyncio
import json
import sys
import traceback
from typing import Literal

from pydantic import BaseModel, Field

from beeai_framework.backend.chat import ChatModel
from beeai_framework.backend.message import UserMessage
from beeai_framework.errors import FrameworkError


async def main() -> None:
    #### DO NOT PUSH THIS TO MAIN! THIS IS A TEMP CHANGE FOR TESTING ####

    model = ChatModel.from_name("ollama:llama3.1")

    class ProfileSchema(BaseModel):
        first_name: str = Field(..., min_length=1)
        last_name: str = Field(..., min_length=1)
        address: str
        age: int = Field(..., min_length=1)
        hobby: str
        xyzabc: Literal["adsdfsa", "gfsd", "hgdh"] | None = None

    response = await model.create_structure(
        schema=ProfileSchema,
        messages=[
            UserMessage("Generate a profile of a citizen of Europe."),
        ],
    )

    print(
        json.dumps(
            response.object.model_dump() if isinstance(response.object, BaseModel) else response.object, indent=4
        )
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except FrameworkError as e:
        traceback.print_exc()
        sys.exit(e.explain())
