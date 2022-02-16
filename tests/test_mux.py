from django.test import TestCase, override_settings

from muxltiproducer import mux


class MuxTests(TestCase):
    @override_settings(MUX_WEBHOOK_SIGNING_SECRET="secret")
    def test_verify_invalid_webhook_signatures(self):
        self.assertFalse(mux.verify_webhook_signature("t=1234,v1=dummy", b"body"))
        self.assertFalse(mux.verify_webhook_signature("t=1234,v1=", b"body"))
        self.assertFalse(mux.verify_webhook_signature("t=1234abcd,v1=", b"body"))
        self.assertFalse(mux.verify_webhook_signature("", b"body"))

    @override_settings(MUX_WEBHOOK_SIGNING_SECRET="erob92t3ipbagicdlnj222h9gf91msfb")
    def test_verify_valid_webhook_signature(self):
        body = b"""{"type":"video.upload.created","request_id":null,"object":{"type":"upload","id":"00bAe2kCB4K006Y9X3HiDJje01z6x1KOZzm4UyPYapUC00k"},"id":"5307615d-4a37-4045-9d12-ddb9cb8e7a2f","environment":{"name":"Development","id":"qunfvh"},"data":{"url":"https://storage.googleapis.com/video-storage-us-east1-uploads/00bAe2kCB4K006Y9X3HiDJje01z6x1KOZzm4UyPYapUC00k?Expires=1646571336&GoogleAccessId=direct-uploads-writer-prod%40mux-cloud.iam.gserviceaccount.com&Signature=FOdP7yIzJ4I6W35pRr9HGqZ%2BriFdChbW6nBacPqJ%2BfWvbZb%2F2MPCQVwk%2FzOPX0kOPAaZBYT0E3S98JVtKLiYmicwthwhtw%2FJv%2BjsZ8iT4yA686nZ70xRDvCLtqN%2BDJI%2FTcRwt1Adw5AwFQ6ROqP1XrFH34L3OeQKUcDXSvn299kahaQv911zQqBDZNVtQiuSQsQ2w2IcHa7mzGsFwfapUxp5k%2BVlATPtCt4g9V7Xc3NHWnRhhY4EHVca%2BZWxkTJ%2B11DCC3ba%2BaFmTx40j65IyFRkAtoP90nugO6pe5j5nb3eq3Wf2w87l70hNsPNQv1Ta%2F4QFIQ4POZOqEp%2BNLh2%2FQ%3D%3D&upload_id=ADPycdu_JEWhcWSaoJar3af-TUPVHpSFIZVTOOcX5U4Zu6URJoad3XCCi34H9bQhdLtxzO7yQR2U5nmETj8qE9jhNSoXSsRWQQ","timeout":172800,"status":"waiting","new_asset_settings":{"playback_policies":["signed"]},"id":"00bAe2kCB4K006Y9X3HiDJje01z6x1KOZzm4UyPYapUC00k","cors_origin":"http://localhost:9630"},"created_at":"2022-03-04T12:55:37.000000Z","attempts":[],"accessor_source":null,"accessor":null}"""
        signature = "t=1646398537,v1=3a336662fd90119b62bb53ea7b208e9b8439fe757d3ceaef8f3c04f0c4d5f187"
        self.assertTrue(mux.verify_webhook_signature(signature, body))
