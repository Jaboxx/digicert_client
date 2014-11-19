from ..queries import Query


class V2Query(Query):
    _base_path = '/services/v2'

    def __init__(self, customer_api_key, **kwargs):
        super(V2Query, self).__init__(customer_api_key=customer_api_key, customer_name=None, **kwargs)
        self.set_header('X-DC-DEVKEY', customer_api_key)
        self.set_header('Content-Type', 'application/json')

    def get_method(self):
        return 'GET'

    def _is_failure_response(self, response):
        return 'errors' in response


class ViewOrderDetailsQuery(V2Query):
    order_id = None

    def __init__(self, customer_api_key, **kwargs):
        super(ViewOrderDetailsQuery, self).__init__(customer_api_key=customer_api_key, **kwargs)
        if self.order_id is None:
            raise KeyError('No value provided for required property "order_id"')

    def get_path(self):
        return '%s/order/certificate/%s' % (self._base_path, self.order_id)

    def _subprocess_response(self, status, reason, response):
        return self._make_response(status, reason, response)


class DownloadCertificateQuery(V2Query):
    order_id = None
    certificate_id = None

    def __init__(self, customer_api_key, **kwargs):
        super(DownloadCertificateQuery, self).__init__(customer_api_key=customer_api_key, **kwargs)
        if self.certificate_id is None and self.order_id is None:
            raise KeyError('No value provided for required properties "certificate_id", "order_id" (at least one is required)')

    def get_path(self):
        return '%s/certificate/%s/download/format/pem_all' % (self._base_path, self.certificate_id)

    def _subprocess_response(self, status, reason, response):
        certs = []
        for cert in response.split('-----'):
            cert = cert.strip()
            if len(cert) and not cert.startswith('BEGIN ') and not cert.startswith('END '):
                certs.append(cert)
        if 3 != len(certs):
            raise RuntimeError('Unexpected number of certificates in certificate chain')
        return self._make_response(status, reason, {
            'certificates': {
                'certificate': '-----BEGIN CERTIFICATE-----\r\n' + certs[0] + '\r\n-----END CERTIFICATE-----',
                'intermediate': '-----BEGIN CERTIFICATE-----\r\n' + certs[1] + '\r\n-----END CERTIFICATE-----',
                'root': '-----BEGIN CERTIFICATE-----\r\n' + certs[2] + '\r\n-----END CERTIFICATE-----'
            }
        })


class MyUserQuery(V2Query):
    def __init__(self, customer_api_key):
        super(MyUserQuery, self).__init__(customer_api_key=customer_api_key)

    def get_path(self):
        return '%s/user/me' % self._base_path

    def _subprocess_response(self, status, reason, response):
        return response


class OrganizationByContainerIdQuery(V2Query):
    def __init__(self, customer_api_key, container_id):
        super(OrganizationByContainerIdQuery, self).__init__(customer_api_key=customer_api_key)
        self.container_id = container_id

    def get_path(self):
        return '%s/organization?container_id=%s' % (self._base_path, self.container_id)

    def _subprocess_response(self, status, reason, response):
        orgs = []
        for entry in response['organizations']:
            orgs.append(entry)
        return orgs


class DomainByContainerIdQuery(V2Query):
    def __init__(self, customer_api_key, container_id):
        super(DomainByContainerIdQuery, self).__init__(customer_api_key=customer_api_key)
        self.container_id = container_id

    def get_path(self):
        return '%s/domain?container_id=%s' % (self._base_path, self.container_id)

    def _subprocess_response(self, status, reason, response):
        domains = []
        for entry in response['domains']:
            domains.append(entry)
        return domains

if __name__ == '__main__':
    pass