import random
import string

from generated.proto import account_pb2

class StorageLayer():
    def __init__(self, db_client):
        self._db = db_client.tgotm

    async def create_new_wish(self, user_id: str) -> str:
        chars = string.ascii_uppercase + string.ascii_lowercase +  string.digits
        wish_id = ""
        while True:
            wish_id = ''.join(random.choice(chars) for _ in range(8))
            print("Try creating new wish for user %s" % (wish_id, user_id))
            if await self._db["user_wishes"].find_one({"wish_id": wish_id, "user_id": user_id}) is None:
                break
        return wish_id

    async def create_new_user(self, email: str, name: str) -> str:
        chars = string.ascii_uppercase + string.ascii_lowercase +  string.digits
        public_id = ""
        while True:
            public_id = ''.join(random.choice(chars) for _ in range(8))
            print("Try creating new user %s for: %s" % (public_id, email))
            if await self._db["accounts"].find_one({"public_id": public_id}) is None:
                break

        print("Creating new user %s for: %s" % (public_id, email))
        new_account = {
            "public_id": public_id,
            "email": email,
            "name": name,
            "avatar_url" : "placeholder.images.com",
        }
        await self._db["accounts"].insert_one(new_account)
        return public_id

    async def get_existing_public_id(self, email: str) -> str:
        if (account := await self._db["accounts"].find_one({"email": email})) is not None:
            return account["public_id"]
        else:
            return ""

    async def get_user_public_id(self, email: str, name: str) -> str:
        public_id = await self.get_existing_public_id(email)
        if not public_id:
            public_id = await self.create_new_user(email, name)
        return public_id

    async def get_user_profile(self, public_id: str) -> account_pb2.Account:
        print("Getting profile for account %s" % public_id)
        account = account_pb2.Account()
        if (existing_account := await self._db["accounts"].find_one({"public_id": public_id})) is not None:
            account.public_id = existing_account["public_id"]
            account.email = existing_account["email"]
            account.name = existing_account["name"]
            account.avatar_url = existing_account["avatar_url"]
        else:
            print("Public id %s not found" % public_id)
            account.public_id = public_id
            account.email = "N/A"
            account.name = "N/A"
            account.avatar_url = "N/A"
        return account

