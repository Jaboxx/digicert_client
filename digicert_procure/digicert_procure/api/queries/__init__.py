#!/usr/bin/env python

from ...api import DigiCertApiRequest
from ...api.responses\
    import OrderViewDetailsSucceededResponse,\
    RetrieveCertificateSucceededResponse,\
    CertificateDetails,\
    PendingReissue,\
    RetrievedCertificate


class DigiCertApiQuery(DigiCertApiRequest):
    """Base class for CQRS-style Query objects."""

    order_id = None

    def __init__(self, customer_api_key, order_id, customer_name=None, **kwargs):
        """
        RetailApiQuery constructor

        :param customer_api_key: the customer's DigiCert API key
        :param order_id: the order ID for the certificate order
        :param customer_name: the customer's DigiCert account number, e.g. '012345'  This parameter
        is optional.  If provided, the DigiCert Retail API will be used; if not, the DigiCert CertCentral API
        will be used.
        :param kwargs:
        :return:
        """
        super(DigiCertApiQuery, self).__init__(customer_api_key, customer_name, **kwargs)
        self.order_id = order_id

        if not 'order_id' in self.__dict__:
            raise RuntimeError('No value provided for required property "order_id"')

    def _get_method(self):
        return 'POST'


class OrderDetailsQuery(DigiCertApiQuery):
    """CQRS-style Query object for viewing the details of a certificate order"""

    def __init__(self, customer_api_key, order_id, customer_name=None, **kwargs):
        """
        Constructs an OrderDetailsQuery, a CQRS-style Query for viewing the status of a certificate order.

        All required parameters must be specified in the constructor positionally or by keyword.
        Optional parameters may be specified via kwargs.

        :param customer_api_key: the customer's DigiCert API key
        :param order_id: the order ID for the certificate order
        :param customer_name: the customer's DigiCert account number, e.g. '012345'  This parameter
        is optional.  If provided, the DigiCert Retail API will be used; if not, the DigiCert CertCentral API
        will be used.
        :param kwargs:
        :return:
        """
        super(OrderDetailsQuery, self).__init__(customer_api_key, order_id, customer_name, **kwargs)

    def _get_path(self):
        return '%s?action=order_view_details' % self._get_base_path()

    def _subprocess_response(self, status, reason, response):
        try:
            rspreturn = response['response']['return']
            return OrderViewDetailsSucceededResponse(status, reason,
                                                     self._certificate_details_from_response(rspreturn),
                                                     self._pending_reissue_from_response(rspreturn))
        except KeyError:
            return OrderViewDetailsSucceededResponse(status, reason, None, None)

    @staticmethod
    def _certificate_details_from_response(response):
        if response:
            try:
                d = response['certificate_details']
                return CertificateDetails(order_id=_value_from_dict(d, 'order_id'),
                                          status=_value_from_dict(d, 'status'),
                                          product_name=_value_from_dict(d, 'product_name'),
                                          validity=_value_from_dict(d, 'validity'),
                                          org_unit=_value_from_dict(d, 'org_unit'),
                                          common_name=_value_from_dict(d, 'common_name'),
                                          sans=_value_from_dict(d, 'sans'),
                                          order_date=_value_from_dict(d, 'order_date'),
                                          valid_from=_value_from_dict(d, 'valid_from'),
                                          valid_till=_value_from_dict(d, 'valid_till'),
                                          server_type=_value_from_dict(d, 'server_type'),
                                          server_type_name=_value_from_dict(d, 'server_type_name'),
                                          site_seal_token=_value_from_dict(d, 'site_seal_token'))
            except KeyError:
                pass
        return None

    @staticmethod
    def _pending_reissue_from_response(response):
        if response:
            try:
                d = response['pending_reissue']
                return PendingReissue(common_name=_value_from_dict(d, 'common_name'),
                                      sans=_value_from_dict(d, 'sans'))
            except KeyError:
                pass
        return None


class RetrieveCertificateQuery(DigiCertApiQuery):
    """CQRS-style Query object for retrieving an issued certificate."""

    def __init__(self, customer_api_key, order_id, customer_name=None, **kwargs):
        """
        Constructs an RetrieveCertificateQuery, a CQRS-style Query for retrieving an issued certificate.

        All required parameters must be specified in the constructor positionally or by keyword.
        Optional parameters may be specified via kwargs.

        :param customer_api_key: the customer's DigiCert API key
        :param order_id: the order ID for the certificate order
        :param customer_name: the customer's DigiCert account number, e.g. '012345'  This parameter
        is optional.  If provided, the DigiCert Retail API will be used; if not, the DigiCert CertCentral API
        will be used.
        :param kwargs:
        :return:
        """
        super(RetrieveCertificateQuery, self).__init__(customer_api_key, order_id, customer_name, **kwargs)

    def _get_path(self):
        return '%s?action=retrieve_certificate' % self._get_base_path()

    def _subprocess_response(self, status, reason, response):
        try:
            rspreturn = response['response']['return']
            return RetrieveCertificateSucceededResponse(status, reason,
                                                        _value_from_dict(rspreturn, 'order_id'),
                                                        _value_from_dict(rspreturn, 'serial'),
                                                        self._certs_from_response(rspreturn))
        except KeyError:
            return RetrieveCertificateSucceededResponse(status, reason, None, None, None)

    @staticmethod
    def _certs_from_response(response):
        if response:
            try:
                d = response['certs']
                return RetrievedCertificate(certificate=_value_from_dict(d, 'certificate'),
                                            intermediate=_value_from_dict(d, 'intermediate'),
                                            root=_value_from_dict(d, 'root'),
                                            pkcs7=_value_from_dict(d, 'pkcs7'))
            except KeyError:
                pass
        return None


def _value_from_dict(d, key, default=None):
    if d and key and key in d:
        return d[key]
    return default


if __name__ == '__main__':
    pass