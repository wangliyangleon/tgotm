from tornado import web, ioloop, escape, auth
from motor import motor_tornado

import os

from generated.proto import wish_item_pb2
from storage_layer import StorageLayer

class BaseHandler(web.RequestHandler):
    def get_current_user(self):
        return self.get_signed_cookie("user_public_id")


class LoginHandler(BaseHandler):
    def get(self):
        self.write("<p>Please login</p><ul>")
        self.write('<li><a href="auth/google">Login with Google</a></li></ul>')


class GoogleOAuth2LoginHandler(web.RequestHandler,
                               auth.GoogleOAuth2Mixin):
    def initialize(self):
        self._storage = StorageLayer(self.settings["db_client"])

    async def get(self):
        if self.get_argument('code', False):
            access = await self.get_authenticated_user(
                redirect_uri='http://localhost:5000/auth/google',
                code=self.get_argument('code'))
            user = await self.oauth2_request(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                access_token=access["access_token"])

            # store into db if it's a new user
            email = escape.xhtml_escape(user["email"])
            name = escape.xhtml_escape(user["name"])
            self.set_signed_cookie("user_public_id", await self._storage.get_user_public_id(email, name))
            self.redirect("/")

        else:
            self.authorize_redirect(
                redirect_uri='http://localhost:5000/auth/google',
                client_id=self.get_google_oauth_settings()['key'],
                scope=['profile', 'email'],
                response_type='code',
                extra_params={'approval_prompt': 'auto'})


class IndexHandler(BaseHandler):
    def initialize(self):
        self._storage = StorageLayer(self.settings["db_client"])

    def populate_wish_item(self, id, name, link_url, shop_type):
        wish_item = wish_item_pb2.WishItem()
        wish_item.id = id
        wish_item.name = name
        link = wish_item.shopping_links.add()
        link.url = link_url
        link.shop_type = shop_type
        return wish_item

    @web.authenticated
    async def get(self):
        logged_in_account = await self._storage.get_user_profile(escape.xhtml_escape(self.current_user))
        wish_items = []
        wish_items.append(
            self.populate_wish_item(1,
                                    "Leica M11",
                                    "https://leica-store.sg/products/leica-m11-silver",
                                    wish_item_pb2.WishItemShoppingLink.ShopType.SHOP_TYPE_UNSPECIFIED))
        wish_items.append(
            self.populate_wish_item(2,
                                    "Leica Elmarit-M 28mm F/2.8 ASPH",
                                    "https://leica-store.sg/products/leica-elmarit-m-28mm-f-2-8-asph-black",
                                    wish_item_pb2.WishItemShoppingLink.ShopType.SHOP_TYPE_UNSPECIFIED))
        wish_items.append(
            self.populate_wish_item(3,
                                    "PlayStation 5",
                                    "https://www.amazon.com/PlayStation-5-Console-CFI-1215A01X/dp/B0BCNKKZ91/ref=sr_1_3?crid=DP4ND9EB4I9J&keywords=ps5&qid=1697793757&sprefix=ps%2Caps%2C312&sr=8-3&th=1",
                                    wish_item_pb2.WishItemShoppingLink.ShopType.SHOP_TYPE_AMAZON))
        self.render("index.html",
                    account=logged_in_account,
                    wish_items=wish_items)

class WishlistHandler(web.RequestHandler):
    def initialize(self):
        self._storage = StorageLayer(self.settings["db_client"])

    def populate_wish_item(self, id, name, link_url, shop_type):
        wish_item = wish_item_pb2.WishItem()
        wish_item.id = id
        wish_item.name = name
        link = wish_item.shopping_links.add()
        link.url = link_url
        link.shop_type = shop_type
        return wish_item

    async def get(self, public_id):
        account = await self._storage.get_user_profile(public_id)

        wish_items = []
        wish_items.append(
            self.populate_wish_item(1,
                                    "Leica M11",
                                    "https://leica-store.sg/products/leica-m11-silver",
                                    wish_item_pb2.WishItemShoppingLink.ShopType.SHOP_TYPE_UNSPECIFIED))
        wish_items.append(
            self.populate_wish_item(2,
                                    "Leica Elmarit-M 28mm F/2.8 ASPH",
                                    "https://leica-store.sg/products/leica-elmarit-m-28mm-f-2-8-asph-black",
                                    wish_item_pb2.WishItemShoppingLink.ShopType.SHOP_TYPE_UNSPECIFIED))
        wish_items.append(
            self.populate_wish_item(3,
                                    "PlayStation 5",
                                    "https://www.amazon.com/PlayStation-5-Console-CFI-1215A01X/dp/B0BCNKKZ91/ref=sr_1_3?crid=DP4ND9EB4I9J&keywords=ps5&qid=1697793757&sprefix=ps%2Caps%2C312&sr=8-3&th=1",
                                    wish_item_pb2.WishItemShoppingLink.ShopType.SHOP_TYPE_AMAZON))
        self.render("wishlist.html",
                    account=account,
                    wish_items=wish_items)


def main():
    settings = {
		"template_path": os.path.join(os.path.dirname(__file__), "templates"),
		"static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "aafDFWcAEefq323gq34rwKadc",
        "login_url": "/login",
        "google_oauth": {"key": "572658144253-2ifc8o8vj8ufml8kt6k2caddi5d4othp.apps.googleusercontent.com", "secret": "VQULx6mUU95euAAXmxoIf9jd"},
        "db_client": motor_tornado.MotorClient("mongodb+srv://wangliyangleon:jdsFsTpNPwZkSKxh@cluster0.skjbcmx.mongodb.net/?retryWrites=true&w=majority"),
		"debug" : True
	}

    app = web.Application(
		[
			(r'/', IndexHandler),
            (r'/login', LoginHandler),
            (r'/auth/google', GoogleOAuth2LoginHandler),
			(r'/([a-zA-Z0-9]+)', WishlistHandler),
			# (r'/ws', WebSocketHandler),
			# (r'/api', ApiHandler),
		], **settings
	)


    port = int(os.environ.get("PORT", 5000))
    print('Listening on port: %s' % port)
    app.listen(port)
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()