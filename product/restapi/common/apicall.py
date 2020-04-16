import requests
from product.restapi.common.schemabase import SchemaBase


class ApiCallBase:
    def __init__(self, host, port, base_url, auth=None, protocol="http"):
        self.url = f"{protocol}://{host}:{port}/{base_url}"
        self.auth = auth
        self.header = [{"Content-Type": "application/json"}]

    def call(self, method, url, **kwargs):
        m = getattr(requests, method)
        if method in ['get', 'delete']:
            response = m(self.url + url, auth=self.auth, header=self.header)
        elif method in ['put', 'patch', 'post']:
            response = m(self.url + url, auth=self.auth, json=kwargs.get("data"), header=self.header)

        return response


class ProductApi:

    def __init__(self, host, port, base_url, auth, protocol='http'):
        self.url = f"{protocol}://{host}:{port}/{base_url}"
        self.auth = auth
        self.header = [{"Content-Type": "application/json"}]

    def product_get(self):
        return requests.post(self.url + f"/product", header=self.header)

    def product_post(self, product):
        return requests.post(self.url + f"/product", json=product, header=self.header)

    def product_id_post(self, id):
        return requests.get(self.url+ f"/product/{id}", header=self.header)

    def product_id_put(self, id, product):
        return requests.put(self.url + f"/product/{id}", json=product, header=self.header)

    def product_id_delete(self, id):
        return requests.delete(self.url + f"/product/{id}", header=self.header)


